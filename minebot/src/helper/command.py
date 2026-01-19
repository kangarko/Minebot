from logging import Logger
from typing import Literal, cast

import hikari
import lightbulb
from lightbulb import ExecutionHook
from lightbulb.prefab import cooldowns
from pydantic import PositiveInt

from core import GlobalState
from debug import get_logger
from model import CommandsKeys
from model.schemas import (
    BasicCommand,
    CommandCooldown,
    LoggedCommandConfig,
    RewardableCommandConfig,
    TransferableCommandConfig,
)
from settings import Settings

# Get logger but with a reduced verbosity for debug messages
logger: Logger = get_logger(__name__)


class CommandHelper:
    def __init__(self, command: CommandsKeys) -> None:
        """
        Initialize a command helper.

        Args:
            command (CommandsKeys): The command key identifier.

        Attributes:
            command_name (str): The lowercase name of the command.
            command_enabled (bool): Whether the command is enabled.
            command_permissions (list[hikari.Permissions]): Permissions required to use the command.
            command_cooldown (Cooldown | None): The cooldown settings for the command.
            command_log_enabled (bool): Whether logging is enabled for the command.
            command_log_channel (PositiveInt): The channel ID for logging.
        """
        self.command_name: str = command.name.lower()
        self._cached_permission_value: int | None = None

        try:
            command_info: BasicCommand = Settings.get(command)

            # Check if command_info is None and handle it
            if command_info is None:
                self._set_defaults()
                return

            # Basic command properties
            self.command_enabled: bool = True
            self.command_cooldown: CommandCooldown | None = command_info.cooldown
            self.command_permissions = self._parse_permissions(command_info.permissions)

            # Log initialization
            self._log_initialization()

            # Handle logging configuration
            self._configure_logging(command_info)

            # Handle reward configuration
            self._configure_reward(command_info)

            # Handle synchronization configuration
            self._configure_synchronization(command_info)

        except Exception as e:
            # Provide a clear error message with the command name and error
            logger.error(f"[Command: {self.command_name}] Initialization FAILED: {str(e)}")
            raise ValueError(f"Failed to initialize command {command.name}: {str(e)}")

    def _set_defaults(self) -> None:
        """Set default values for command properties."""
        self.command_enabled = False
        self.command_permissions = [hikari.Permissions.NONE]
        self.command_cooldown = None
        self.command_log_enabled = False
        self.command_log_channel = None

        logger.debug(
            f"[Command: {self.command_name}] Initialized with defaults - Enabled: {self.command_enabled}, "
            f"Permissions: {[p.name for p in self.command_permissions]}"
        )

    def _parse_permissions(self, permission_strings: list[str]) -> list[hikari.Permissions]:
        """Parse string permissions into hikari.Permissions enum values."""
        return [
            hikari.Permissions.NONE if p == "NONE" else hikari.Permissions[p]
            for p in permission_strings
        ]

    def _log_initialization(self) -> None:
        """Log basic command initialization details."""
        logger.debug(
            f"[Command: {self.command_name}] Initialized - Enabled: {self.command_enabled}, "
            f"Permissions: {[p.name for p in self.command_permissions]}"
        )

    def _configure_logging(self, command_info: BasicCommand) -> None:
        """Configure logging properties if available."""
        # Default values
        self.command_log_channel: PositiveInt | None = None

        if isinstance(command_info, LoggedCommandConfig):
            self.command_log_channel = command_info.log
            logger.debug(
                f"[Command: {self.command_name}] Logging configured - Enabled: {bool(self.command_log_channel)}, "
                f"Channel: {self.command_log_channel}"
            )

    def _configure_reward(self, command_info: BasicCommand) -> None:
        """Configure command reward settings if applicable."""
        # Default values
        self.command_reward_mode: str | None = None
        self.command_reward_role: list[PositiveInt] | None = None
        self.command_reward_item: dict[str, list[str]] | None = None

        if isinstance(command_info, RewardableCommandConfig) and command_info.reward is not None:
            self.command_reward_mode = command_info.reward.mode

            # Convert single PositiveInt to list
            if command_info.reward.role is not None:
                self.command_reward_role = (
                    [command_info.reward.role]
                    if isinstance(command_info.reward.role, int)
                    else command_info.reward.role
                )

            # Convert string values to list[str]
            if command_info.reward.item is not None:
                self.command_reward_item = {
                    k: [v] if isinstance(v, str) else v for k, v in command_info.reward.item.items()
                }

            logger.debug(
                f"[Command: {self.command_name}] Reward configured - "
                f"Enabled: {bool(self.command_reward_mode)}, "
                f"Role: {self.command_reward_role}, "
                f"Item: {self.command_reward_item}"
            )

    def _configure_synchronization(self, command_info: BasicCommand) -> None:
        """Configure command synchronization settings if applicable."""
        # Default values
        self.command_synchronization_minecraft_to_discord: bool = False
        self.command_synchronization_discord_to_minecraft: bool = False

        if (
            isinstance(command_info, TransferableCommandConfig)
            and command_info.synchronization is not None
        ):
            self.command_synchronization_minecraft_to_discord = (
                command_info.synchronization.minecraft_to_discord
            )
            self.command_synchronization_discord_to_minecraft = (
                command_info.synchronization.discord_to_minecraft
            )

            if enabled := bool(
                self.command_synchronization_minecraft_to_discord
                or self.command_synchronization_discord_to_minecraft
            ):
                GlobalState.commands.add_sync_state(
                    self.command_name,
                    self.command_synchronization_minecraft_to_discord,
                    self.command_synchronization_discord_to_minecraft,
                )

            logger.debug(
                f"[Command: {self.command_name}] Synchronization configured - "
                f"Enabled: {enabled}, "
                f"MC to Discord: {self.command_synchronization_minecraft_to_discord}, "
                f"Discord to MC: {self.command_synchronization_discord_to_minecraft}"
            )

    def get_loader(self) -> lightbulb.Loader:
        """
        Get the lightbulb command loader for the command helper.

        Returns:
            lightbulb.Loader: A loader instance that uses the command_enabled status as a condition.
        """
        logger.info(
            f"[Command: {self.command_name}] Creating command loader "
            f"(Status: {'ENABLED' if self.command_enabled else 'DISABLED'})"
        )
        return lightbulb.Loader(lambda: self.command_enabled)

    def get_permissions(self) -> int:
        """
        Get the permissions required for the command as a combined integer value.

        Returns:
            int: The combined permission value as expected by Discord's API.
        """
        # Return cached value if available
        if self._cached_permission_value is not None:
            return self._cached_permission_value

        # Special case: if NONE is in the permissions list, return 0
        if any(p == hikari.Permissions.NONE for p in self.command_permissions):
            logger.debug(f"[Command: {self.command_name}] Using NONE permission (value: 0)")
            self._cached_permission_value = 0
            return 0

        # Combine permissions
        combined_permissions = 0
        for permission in self.command_permissions:
            combined_permissions |= permission.value

        logger.debug(
            f"[Command: {self.command_name}] Permissions: {[p.name for p in self.command_permissions]} → {combined_permissions}"
        )

        # Cache the result
        self._cached_permission_value = combined_permissions
        return combined_permissions

    def generate_hooks(
        self,
        additional_hooks: ExecutionHook | list[ExecutionHook] | None = None,
    ) -> list[ExecutionHook]:
        """
        Generate a list of execution hooks for the command.

        Args:
            additional_hooks: Optional hook(s) to include with command hooks.

        Returns:
            list[lb.ExecutionHook]: A list of execution hooks, including cooldowns if configured.
        """
        logger.debug(f"[Command: {self.command_name}] Generating execution hooks")
        hooks = []

        # Add cooldown if configured
        if cooldown_hook := self._get_cooldown():
            hooks.append(cooldown_hook)

        # Add additional hooks if provided
        if additional_hooks:
            if isinstance(additional_hooks, list):
                hooks.extend(additional_hooks)
            else:
                hooks.append(additional_hooks)

        return hooks

    def get_log_channel_id(self) -> PositiveInt | None:
        """
        Get the ID of the channel where command logs should be sent.

        Returns:
            PositiveInt | None: The channel ID if logging is enabled, None otherwise.
        """
        return self.command_log_channel

    def get_reward_role_ids(self) -> list[PositiveInt] | None:
        """
        Get the roles that should be rewarded for using the command.

        Returns:
            list[PositiveInt] | None: The role ID(s) if rewards are enabled, None otherwise.
        """
        return self.command_reward_role

    def get_reward_items(self) -> dict[str, list[str]] | None:
        """
        Get the items that should be rewarded for using the command.

        Returns:
            dict[str, list[str]] | None: The item data if rewards are enabled, None otherwise.
        """
        if self.command_reward_item is None:
            return None

        final_item_reward: dict[str, list[str]] = {}
        default_reward: list[str] | None = self.command_reward_item.get("defualt", None)

        for server_name, items in self.command_reward_item.items():
            if GlobalState.minecraft.contains_server(server_name):
                final_item_reward[server_name] = items
            elif server_name != "default":
                final_item_reward[server_name] = default_reward or []

    def has_synchronization_minecraft_to_discord(self) -> bool:
        """
        Check if the command has synchronization from Minecraft to Discord enabled.

        Returns:
            bool: True if synchronization is enabled, False otherwise.
        """
        return self.command_synchronization_minecraft_to_discord

    def has_synchronization_discord_to_minecraft(self) -> bool:
        """
        Check if the command has synchronization from Discord to Minecraft enabled.

        Returns:
            bool: True if synchronization is enabled, False otherwise.
        """
        return self.command_synchronization_discord_to_minecraft

    async def synchronize_to_minecraft(
        self, server: str, command_type: str, args: dict[str, str] | None = None
    ) -> bool:
        from websocket import WebSocketManager
        from websocket.schemas.event import CommandExecutedSchema

        if not self.command_synchronization_discord_to_minecraft:
            return False

        return await WebSocketManager.send_message(
            CommandExecutedSchema(
                server=server, command_type=command_type, executor="MineBot", args=args
            )
        )

    def _get_cooldown(self) -> ExecutionHook | None:
        """
        Get the configured cooldown as a lightbulb execution hook.

        Returns:
            lightbulb.ExecutionHook | None: The configured cooldown hook or None if no cooldown is set.
        """
        if not self.command_cooldown:
            logger.debug(f"[Command: {self.command_name}] No cooldown configured")
            return None

        try:
            window_length: PositiveInt = self.command_cooldown.window_length
            allowed_invocations: PositiveInt = self.command_cooldown.allowed_invocations
            bucket: str = self.command_cooldown.bucket
            algorithm: str = self.command_cooldown.algorithm

            # Validate bucket type with explicit error message
            valid_buckets = ["global", "user", "channel", "guild"]
            if bucket not in valid_buckets:
                raise ValueError(
                    f"Invalid bucket type: '{bucket}'. Must be one of: {valid_buckets}"
                )

            bucket_literal = cast(Literal["global", "user", "channel", "guild"], bucket)

            logger.debug(
                f"[Command: {self.command_name}] Configuring {algorithm} cooldown: "
                f"{allowed_invocations} invocations per {window_length}s ({bucket})"
            )

            # Dictionary-based cooldown creation
            cooldown_creators = {
                "fixed_window": lambda: cooldowns.fixed_window(
                    window_length=window_length,
                    allowed_invocations=allowed_invocations,
                    bucket=bucket_literal,
                ),
                "sliding_window": lambda: cooldowns.sliding_window(
                    window_length=window_length,
                    allowed_invocations=allowed_invocations,
                    bucket=bucket_literal,
                ),
            }

            if algorithm not in cooldown_creators:
                raise ValueError(f"Unknown cooldown algorithm: {algorithm}")

            return cooldown_creators[algorithm]()

        except (ValueError, KeyError, AttributeError) as e:
            # More specific exception handling
            logger.error(f"[Command: {self.command_name}] Failed to create cooldown: {str(e)}")
            raise ValueError(
                f"Failed to configure cooldown for {self.command_name}: {str(e)}"
            ) from e
