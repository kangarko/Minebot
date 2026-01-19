import asyncio
from logging import Logger

import hikari
from pydantic import PositiveInt

from core import GlobalState
from database.schemas import UserSchema
from database.services import UserService
from debug import get_logger
from model import MessageType, SecretKeys
from model.schemas import UserReward
from settings.json_wrapper import Settings
from websocket.schemas import ResponseAwaitableSchema
from websocket.schemas.request import (
    DispatchCommandSchema,
    SendGlobalMessageSchema,
    SendPlayerMessageSchema,
    SendServerMessageSchema,
)
from websocket.schemas.response import PlayerServerCheckSchema, PlayerStatusCheckSchema

logger: Logger = get_logger(__name__)


class MinecraftHelper:
    @staticmethod
    async def _resolve_identifier(
        user: hikari.User | None = None,
        username: str | None = None,
        uuid: str | None = None,
    ) -> tuple[str, bool]:
        """
        Resolves a player identifier (username or UUID) from the provided parameters.

        Args:
            user: Discord user to check (their UUID will be retrieved from database)
            username: Minecraft username
            uuid: Minecraft UUID

        Returns:
            Tuple containing (identifier, is_from_database)

        Raises:
            ValueError: If invalid parameter combination is provided
        """
        # If user is provided, get their UUID from database
        if user:
            if username or uuid:
                logger.error(
                    f"Invalid parameter combination: user={user.id}, username={username}, uuid={uuid}"
                )
                raise ValueError("When 'user' is provided, 'username' and 'uuid' must be None")

            logger.debug(f"Looking up Minecraft UUID for Discord user {user.id}")
            schema: UserSchema | None = await UserService.get_user(user.id)
            if not schema or not schema.minecraft_uuid:
                logger.debug(f"No Minecraft UUID found for Discord user {user.id}")
                return "", False

            uuid = schema.minecraft_uuid
            logger.debug(f"Found Minecraft UUID {uuid} for Discord user {user.id}")
            return uuid, True

        # Validate we have exactly one identifier
        if (username is None) == (uuid is None):  # Check if both are None or both are not None
            logger.error(f"Invalid parameter combination: username={username}, uuid={uuid}")
            raise ValueError("Exactly one of 'username' or 'uuid' must be provided")

        # Return the identifier
        return username or uuid or "", False

    @staticmethod
    async def _get_player_websocket_response(
        schema: ResponseAwaitableSchema,
        response_timeout: float = 1.0,
    ) -> None:
        """
        Send schema to WebSocket and wait for response.

        Args:
            schema: The schema to send
            response_timeout: Timeout for waiting for response
        """
        from websocket import WebSocketManager

        await WebSocketManager.send_message(schema)
        logger.debug(f"Waiting {response_timeout}s for WebSocket response")
        await asyncio.sleep(response_timeout)

    @staticmethod
    def check_servers_available() -> bool:
        """Check if any Minecraft servers are available."""
        if not GlobalState.minecraft.get_servers():
            logger.debug("No Minecraft servers available for the requested operation")
            return False
        return True

    @staticmethod
    async def fetch_player_status(
        user: hikari.User | None = None,
        username: str | None = None,
        uuid: str | None = None,
        response_timeout: float = 1.0,
    ) -> bool:
        """
        Check if a Minecraft player is online.

        Args:
            user: Discord user to check (their UUID will be retrieved from database)
            username: Minecraft username (mutually exclusive with user and uuid)
            uuid: Minecraft UUID (mutually exclusive with user and username)
            response_timeout: Timeout for the response from the websocket

        Returns:
            Whether the player is online

        Raises:
            ValueError: If invalid parameter combination is provided
        """
        if not MinecraftHelper.check_servers_available():
            return False

        logger.debug(
            f"Checking player status with: user={user and user.id}, username={username}, uuid={uuid}"
        )

        identifier, from_db = await MinecraftHelper._resolve_identifier(user, username, uuid)
        if not identifier:
            return False

        logger.debug(f"Using identifier: {identifier}")

        # Quick check if already in cache before making request
        if GlobalState.minecraft.check_player_online(identifier):
            logger.debug(f"Player {identifier} found in cache, returning online status")
            return True

        # Request status check from websocket
        logger.debug(f"Player {identifier} not in cache, requesting status from WebSocket")
        await MinecraftHelper._get_player_websocket_response(
            PlayerStatusCheckSchema(
                username=None if from_db else username, uuid=identifier if from_db else uuid
            ),
            response_timeout,
        )

        is_online = GlobalState.minecraft.check_player_online(identifier)
        logger.debug(f"Player {identifier} is {'online' if is_online else 'offline'}")
        return is_online

    @staticmethod
    async def fetch_player_uuid(username: str, response_timeout: float = 1.0) -> str | None:
        """
        Fetches the UUID for a given Minecraft player username.

        This function checks if the player exists by calling fetch_player_status, and if the
        player exists, retrieves the UUID from the PLAYER_UUIDS cache.

        Args:
            username (str): The Minecraft player username to get the UUID for.
            response_timeout (float, optional): Maximum time to wait for a response from
                the Minecraft API, in seconds. Defaults to 1.0.

        Returns:
            str | None: The player's UUID if found, None otherwise.
        """
        if await MinecraftHelper.fetch_player_status(
            username=username, response_timeout=response_timeout
        ):
            if bool(UUID := GlobalState.minecraft.get_player_uuid(username)):
                logger.debug(f"UUID for {username} found: {UUID}")
                return UUID

    @staticmethod
    async def fetch_player_server(
        user: hikari.User | None = None,
        username: str | None = None,
        uuid: str | None = None,
        response_timeout: float = 1.0,
    ) -> str | None:
        """
        Check which server a Minecraft player is currently on.

        Args:
            user: Discord user to check (their UUID will be retrieved from database)
            username: Minecraft username (mutually exclusive with user and uuid)
            uuid: Minecraft UUID (mutually exclusive with user and username)
            response_timeout: Timeout for the response from the websocket

        Returns:
            Server name if player is online, None otherwise

        Raises:
            ValueError: If invalid parameter combination is provided
        """
        if not MinecraftHelper.check_servers_available():
            return None

        logger.debug(
            f"Checking player server with: user={user and user.id}, username={username}, uuid={uuid}"
        )

        identifier, from_db = await MinecraftHelper._resolve_identifier(user, username, uuid)
        if not identifier:
            return None

        logger.debug(f"Using identifier: {identifier}")

        # Quick check if already in cache before making request
        if SERVER := GlobalState.minecraft.get_player_server(identifier):
            logger.debug(f"Player {identifier} found in cache, returning server: {SERVER}")
            return SERVER

        # Check online status first, this already includes waiting for the response
        is_online = await MinecraftHelper.fetch_player_status(
            uuid=identifier if from_db else uuid,
            username=None if from_db else username,
            response_timeout=response_timeout,
        )

        if not is_online:
            logger.debug(f"Player {identifier} is offline, cannot fetch server")
            return None

        # After status check, see if server info was populated
        if SERVER := GlobalState.minecraft.get_player_server(identifier):
            logger.debug(f"Server found in cache after status check: {SERVER}")
            return SERVER

        # If only one server is available, we know the player must be there
        if len(SERVERS := GlobalState.minecraft.get_servers()) == 1:
            logger.debug(f"Only one server available: {SERVERS[0]}")
            return SERVERS[0]

        # If we need to explicitly request server info
        logger.debug(f"Player {identifier} is online but server unknown, requesting from WebSocket")
        await MinecraftHelper._get_player_websocket_response(
            PlayerServerCheckSchema(
                username=None if from_db else username, uuid=identifier if from_db else uuid
            ),
            response_timeout,
        )

        server = GlobalState.minecraft.get_player_server(identifier)
        logger.debug(f"Player {identifier} is on server: {server}")
        return server

    @staticmethod
    async def send_player_message(
        message_type: MessageType,
        message: str,
        user: hikari.User | None = None,
        username: str | None = None,
        uuid: str | None = None,
        response_timeout: float = 1.0,
    ) -> bool:
        """
        Send a message to a specific Minecraft player.

        Args:
            message_type: Type of message to send
            message: Content of the message
            user: Discord user (their UUID will be retrieved from database)
            username: Minecraft username (mutually exclusive with user and uuid)
            uuid: Minecraft UUID (mutually exclusive with user and username)
            response_timeout: Timeout for the response from the websocket

        Returns:
            Whether the message was sent successfully

        Raises:
            ValueError: If invalid parameter combination is provided
        """
        if not MinecraftHelper.check_servers_available():
            return False

        logger.debug(
            f"Sending message to player with: user={user and user.id}, username={username}, uuid={uuid}"
        )

        identifier, from_db = await MinecraftHelper._resolve_identifier(user, username, uuid)
        if not identifier:
            return False

        # Check online status first
        is_online = await MinecraftHelper.fetch_player_status(
            uuid=identifier if from_db else uuid,
            username=None if from_db else username,
            response_timeout=response_timeout,
        )

        if not is_online:
            logger.debug(f"Player {identifier} is offline, cannot send message")
            return False

        from websocket import WebSocketManager

        await WebSocketManager.send_message(
            SendPlayerMessageSchema(
                username=None if from_db else username,
                uuid=identifier if from_db else uuid,
                message_type=message_type,
                message=message,
            )
        )
        # Truncate message for logging if too long
        logger.debug(
            f"Message sent to player {identifier}: {message if len(message) <= 50 else message[:47] + '...'}"
        )
        return True

    @staticmethod
    async def send_global_message(message_type: MessageType, message: str) -> bool:
        """
        Send a message to all online players across all Minecraft servers.

        Args:
            message_type: Type of message to send
            message: Content of the message

        Returns:
            Whether the message was sent successfully
        """
        if not MinecraftHelper.check_servers_available():
            return False

        logger.debug(f"Sending global message: {message}")

        from websocket import WebSocketManager

        await WebSocketManager.send_message(
            SendGlobalMessageSchema(
                message_type=message_type,
                message=message,
            )
        )
        return True

    @staticmethod
    async def send_server_message(message_type: MessageType, message: str, server: str) -> bool:
        """
        Send a message to all players on a specific Minecraft server.

        Args:
            message_type: Type of message to send
            message: Content of the message
            server: Name of the target Minecraft server

        Returns:
            Whether the message was sent successfully
        """
        if not MinecraftHelper.check_servers_available():
            return False

        if not GlobalState.minecraft.contains_server(server):
            logger.warning(f"Server '{server}' not found in available servers")
            return False

        logger.debug(
            f"Sending server message to {server}: {message if len(message) <= 50 else message[:47] + '...'}"
        )

        from websocket import WebSocketManager

        await WebSocketManager.send_message(
            SendServerMessageSchema(
                server=server,
                message_type=message_type,
                message=message,
            )
        )
        return True

    @staticmethod
    async def dispatch_command(server: str, commands: str | list[str]) -> bool:
        """
        Dispatch a command to a specific Minecraft server.

        Args:
            commands: Command(s) to dispatch
            server: Name of the target Minecraft server

        Returns:
            Whether the command was dispatched successfully

        Raises:
            ValueError: If the server is not found in available servers
        """
        if not MinecraftHelper.check_servers_available():
            return False

        if not GlobalState.minecraft.contains_server(server):
            logger.warning(f"Server '{server}' not found in available servers")
            raise ValueError(f"Server '{server}' not found in available servers")

        # Import inside the method to avoid circular imports
        from websocket import WebSocketManager

        logger.debug(f"Dispatching command(s) to server {server}")
        await WebSocketManager.send_message(DispatchCommandSchema(server=server, commands=commands))
        return True

    @staticmethod
    def _process_items(items: list[str], username: str, uuid: str) -> list[str]:
        """Process items by replacing placeholders with actual values."""
        return [
            item.replace("{minecraft_username}", username).replace("{minecraft_uuid}", uuid)
            if isinstance(item, str)
            else item
            for item in items
        ]

    @staticmethod
    async def add_rewards(user: hikari.User, rewards: UserReward | None) -> bool:
        """
        Add rewards to a user including Discord roles and Minecraft items.

        Args:
            user: The Discord user to reward
            rewards: The reward configuration

        Returns:
            True if any rewards were successfully added, False otherwise
        """
        if not rewards:
            logger.debug(f"No rewards to add for user {user.id}")
            return False

        success = False
        role_reward: list[PositiveInt] | None = rewards.role  # type: ignore
        item_reward: dict[str, list[str]] | None = rewards.item  # type: ignore

        # Process role rewards
        if role_reward:
            try:
                guild: hikari.RESTGuild = await GlobalState.bot.get_bot().rest.fetch_guild(
                    Settings.get(SecretKeys.DEFAULT_GUILD)
                )

                for role_id in role_reward:
                    try:
                        await GlobalState.bot.get_bot().rest.add_role_to_member(
                            guild=guild, user=user, role=role_id
                        )
                        success = True
                    except Exception as e:
                        logger.error(f"Failed to assign role {role_id} to user {user.id}: {e}")
            except Exception as e:
                logger.error(f"Failed to fetch guild for role assignment: {e}")

        # Process item rewards
        if item_reward:
            user_data: UserSchema | None = await UserService.get_user(user.id)

            if user_data and user_data.minecraft_username and user_data.minecraft_uuid:
                username = user_data.minecraft_username
                uuid = user_data.minecraft_uuid
                default_reward = item_reward.get("default", [])
                final_item_reward: dict[str, list[str]] = {}

                # Map server names to their specific rewards or default rewards
                for server_name, items in item_reward.items():
                    if server_name == "default":
                        continue

                    if GlobalState.minecraft.contains_server(server_name):
                        # Use server-specific rewards
                        final_item_reward[server_name] = MinecraftHelper._process_items(
                            items, username, uuid
                        )
                    elif default_reward:
                        # Use default rewards for servers not explicitly configured
                        final_item_reward[server_name] = MinecraftHelper._process_items(
                            default_reward, username, uuid
                        )

                # Add items to user inventory in database
                try:
                    for server_name, items in final_item_reward.items():
                        if items:  # Only process non-empty item lists
                            await UserService.add_item(user.id, server_name, items)
                            success = True
                except Exception as e:
                    logger.error(f"Failed to add item rewards for user {user.id}: {e}")

        return success

    @staticmethod
    async def give_rewards(user: hikari.User | None = None, user_id: int | None = None) -> bool:
        """
        Give rewards to a user.

        Args:
            user: Discord user (their UUID will be retrieved from database)
            user_id: Discord user ID (alternative to user)

        Returns:
            Whether the rewards were given successfully
        """
        # Validate input parameters
        if (user is None) == (user_id is None):
            logger.error("Exactly one of 'user' or 'user_id' must be provided")
            return False

        # Get the user ID
        actual_user_id: hikari.Snowflake | int = user.id if user else user_id  # type: ignore

        # Get user data and validate rewards exist
        user_data: UserSchema | None = await UserService.get_user(int(actual_user_id))
        if not user_data or not user_data.reward_inventory:
            logger.debug(f"User {actual_user_id} not found or has no rewards")
            return False

        # Check if user is online and get their server
        server: str | None = await MinecraftHelper.fetch_player_server(
            uuid=user_data.minecraft_uuid
        )
        if not server:
            logger.debug(f"User {actual_user_id} not online on any server")
            return False

        # Check if user has rewards for current server
        rewards: list[str] | None = user_data.reward_inventory.get(server)
        if not rewards or len(rewards) == 0:
            logger.debug(f"No rewards found for user {actual_user_id} on server {server}")
            return False

        # Dispatch commands and update user data
        try:
            if await MinecraftHelper.dispatch_command(server=server, commands=rewards):
                # Clear the rewards immediately after successful dispatch
                user_data.reward_inventory[server] = []
                await UserService.create_or_update_user(user_data)
                logger.debug(f"Rewards dispatched successfully for user {actual_user_id}")
                return True
        except ValueError as e:
            logger.error(f"Failed to dispatch commands: {e}")

        logger.debug(f"Failed to dispatch rewards for user {actual_user_id}")
        return False
