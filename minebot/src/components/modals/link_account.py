from hikari import RESTGuild
from lightbulb.components.modals import Modal, ModalContext, TextInput
from pydantic import PositiveInt

from core import GlobalState
from database.schemas import UserSchema
from database.services import UserService
from exceptions.command import CommandExecutionError
from helper import (
    CommandHelper,
    MessageHelper,
    ModalHelper,
)
from model import CommandsKeys, MessageKeys, ModalKeys, SecretKeys
from model.message import CommandMessageKeys
from model.schemas import (
    LinkAccountConfirmationModal,
    LoggedRewardableCommandConfig,
    UserReward,
)
from settings import Localization, Settings


class LinkAccountConfirmModal(Modal):
    """
    A modal dialog for confirming the link between a Discord account and a Minecraft account.

    This modal presents a confirmation code input field to the user. If the code entered
    matches the expected code, the user's Discord account will be linked to their Minecraft
    account in the database. Success or failure messages are sent to both the user and a log channel.
    """

    def __init__(
        self,
        username: str,
        uuid: str,
        code: str,
        user_locale: str,
        helper: CommandHelper,
    ) -> None:
        # Get localized modal data based on user's locale
        modal_data: LinkAccountConfirmationModal = Localization.get(
            ModalKeys.LINK_ACCOUNT_CONFIRMATION, locale=user_locale
        )

        self.title: str = modal_data.title
        # Create the code input field with appropriate constraints
        self.input: TextInput = ModalHelper.get_field(
            instance=self, key=modal_data.fields.code, min_lenght=10, max_length=10
        )

        # Store data as private attributes for later use
        self._username: str = username
        self._uuid: str = uuid
        self._code: str = code  # Store the expected confirmation code
        self._user_locale: str = user_locale
        self._helper: CommandHelper = helper

    async def _send_messages(self, ctx: ModalContext, success: bool) -> None:
        """
        Helper method to send both user and log messages about account linking.

        Sends appropriate localized messages to both the user and the log channel
        based on whether the account linking was successful.
        """
        # Select appropriate message keys based on success/failure
        user_key: CommandMessageKeys = (
            MessageKeys.commands.LINK_ACCOUNT_USER_SUCCESS
            if success
            else MessageKeys.commands.LINK_ACCOUNT_USER_FAILURE
        )
        log_key: CommandMessageKeys = (
            MessageKeys.commands.LINK_ACCOUNT_LOG_SUCCESS
            if success
            else MessageKeys.commands.LINK_ACCOUNT_LOG_FAILURE
        )

        # Common parameters for both messages
        default_params: dict[str, str] = {
            "discord_username": ctx.user.username,
            "discord_user_id": str(ctx.user.id),
            "discord_user_mention": ctx.user.mention,
            "minecraft_username": self._username,
            "minecraft_uuid": self._uuid,
        }

        # Send message to the user who submitted the modal
        await MessageHelper(key=user_key, locale=self._user_locale, **default_params).send_response(
            ctx,
            ephemeral=True,  # Make message only visible to the user
        )

        # Send message to the bot's log channel with additional Discord user details
        await MessageHelper(key=log_key, **default_params).send_to_log_channel(self._helper)

    def _process_items(self, items: list[str], username: str, uuid: str) -> list[str]:
        return [
            item.replace("{minecraft_username}", username).replace("{minecraft_uuid}", uuid)
            if isinstance(item, str)
            else item
            for item in items
        ]

    async def _give_rewards(
        self, ctx: ModalContext, username: str, uuid: str
    ) -> dict[str, list[str]] | None:
        """
        Award configured rewards to a user upon successful account linking.

        This method handles two types of rewards:
        1. Discord role rewards - Assigns roles to the user in the Discord guild
        2. Minecraft item rewards - Records items to be granted in different Minecraft servers

        Args:
            ctx: Modal context containing user information and client

        Returns:
            A dictionary mapping Minecraft server names to lists of item rewards,
            or None if no rewards are configured
        """
        # Fetch reward configuration from settings
        data: LoggedRewardableCommandConfig = Settings.get(CommandsKeys.LINK_ACCOUNT)
        rewards: UserReward | None = data.reward

        if rewards is None:
            return None

        # Extract role and item rewards from the configuration
        role_reward: list[PositiveInt] | None = rewards.role  # type: ignore
        item_reward: dict[str, list[str]] | None = rewards.item  # type: ignore
        final_item_reward: dict[str, list[str]] = {}

        # Process Discord role rewards
        if role_reward:
            try:
                guild: RESTGuild = await ctx.client.rest.fetch_guild(
                    Settings.get(SecretKeys.DEFAULT_GUILD)
                )

                # Assign each configured role to the user
                for role_id in role_reward:
                    try:
                        await ctx.client.rest.add_role_to_member(
                            guild=guild, user=ctx.user, role=role_id
                        )
                    except Exception as e:
                        # Log error and raise a command execution error
                        raise CommandExecutionError(f"Failed to assign role {role_id}: {e}")
            except Exception as e:
                # Log error and raise a command execution error
                raise CommandExecutionError(f"Failed to assign roles: {e}")

        # Process Minecraft item rewards
        if item_reward:
            default_reward: list[str] | None = item_reward.get("default", None)

            # Map server names to their specific rewards or default rewards
            for server_name, items in item_reward.items():
                if GlobalState.minecraft.contains_server(server_name):
                    # Use server-specific rewards
                    final_item_reward[server_name] = self._process_items(items, username, uuid)
                elif server_name != "default":  # Skip the default key itself
                    # Use default rewards for non-server keys
                    final_item_reward[server_name] = (
                        self._process_items(default_reward, username, uuid)
                        if default_reward
                        else []
                    )

            return final_item_reward

        # Return None if there are no item rewards
        return None

    async def on_submit(self, ctx: ModalContext) -> None:
        """
        Handle modal submission.

        Validates the confirmation code entered by the user. If valid, links the
        Discord account to the Minecraft account in the database and sends success
        messages. If invalid, sends failure messages.
        """
        # Validate that the entered code matches the expected code
        if self._code != ctx.value_for(self.input):
            # If codes don't match, send failure messages and exit
            await self._send_messages(ctx, success=False)
            return

        # Create or update user record in the database with Minecraft account details
        await UserService.create_or_update_user(
            UserSchema(
                id=ctx.user.id,
                locale=self._user_locale,
                minecraft_username=self._username,
                minecraft_uuid=self._uuid,
                reward_inventory=await self._give_rewards(ctx, self._username, self._uuid),
            ),
            preserve_existing=False,
        )

        # Send success messages to both user and log channel
        await self._send_messages(ctx, success=True)
