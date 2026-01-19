from datetime import datetime, timedelta, timezone
from logging import Logger
from typing import Awaitable, Callable, Final

import hikari
import lightbulb
import toolbox

from core import GlobalState
from database.schemas import TemporaryActionSchema
from database.services import TemporaryActionService
from debug import get_logger
from helper import MessageHelper
from model import MessageKeys, PunishmentType, SecretKeys
from settings import Settings

logger: Logger = get_logger(__name__)


class PunishmentHelper:
    _client: lightbulb.Client | None = None
    _bot_member: hikari.Member | None = None

    @classmethod
    def _get_client(cls) -> lightbulb.Client:
        """Get and cache the bot client if not already cached."""
        if cls._client is None:
            cls._client = GlobalState.bot.get_client()
            logger.debug("Client instance cached")
        return cls._client

    @classmethod
    def _get_bot_member(cls) -> hikari.Member:
        """Get and cache the bot member if not already cached."""
        if cls._bot_member is None:
            cls._bot_member = GlobalState.bot.get_member()
            logger.debug("Bot member instance cached")
        return cls._bot_member

    @classmethod
    def can_moderate(
        cls,
        target: hikari.Member,
        moderator: hikari.Member,
        permission: hikari.Permissions = hikari.Permissions.NONE,
    ) -> bool:
        """Check if both moderator and bot can moderate the target."""
        logger.debug(f"Checking moderation: moderator={moderator.id}, target={target.id}")
        try:
            bot_member = cls._get_bot_member()
            return toolbox.can_moderate(moderator, target, permission) and toolbox.can_moderate(
                bot_member, target, permission
            )
        except ValueError:
            logger.debug("Failed to get bot member, cannot moderate")
            return False

    @staticmethod
    def get_reason(reason: str | None, locale: str | hikari.Locale | None) -> tuple[str, str]:
        """Get reason for a punishment action with localization support."""
        if reason:
            return reason, reason

        if locale is None:
            message = MessageHelper(MessageKeys.general.NO_REASON)._decode_plain()
            return message, message

        messages = MessageHelper(
            MessageKeys.general.NO_REASON, user_locale=locale
        ).get_localized_message_pair("text")

        return (str(messages[0]), str(messages[1]))

    @staticmethod
    def _ensure_timezone_aware(dt: datetime | None) -> datetime | None:
        """Ensure a datetime is timezone aware, using UTC if needed."""
        if dt and dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt

    @classmethod
    async def schedule_punishment_tasks(cls) -> None:
        """Schedule tasks for temporary punishments."""
        logger.debug("Scheduling punishment tasks")
        try:
            client = cls._get_client()
        except ValueError:
            logger.debug("Failed to get client, cannot schedule punishment tasks")
            return

        temp_actions = await TemporaryActionService.get_all_temporary_actions()
        if not temp_actions:
            logger.debug("No temporary actions found, nothing to schedule")
            return

        logger.debug(f"Retrieved {len(temp_actions)} temporary actions")
        guild = Settings.get(SecretKeys.DEFAULT_GUILD)
        no_reason = MessageHelper(MessageKeys.general.NO_REASON)._decode_plain()
        now = datetime.now(timezone.utc)

        handlers = {
            PunishmentType.BAN: cls._handle_ban_action,
            PunishmentType.TIMEOUT: cls._handle_timeout_action,
        }

        for action in temp_actions:
            if action.id is None:
                continue

            handler = handlers.get(getattr(PunishmentType, action.punishment_type.upper()))
            if handler:
                await handler(client, guild, action, now, no_reason)
            else:
                logger.warning(f"Unknown punishment type: {action.punishment_type}")

    @classmethod
    async def _handle_ban_action(
        cls,
        client: lightbulb.Client,
        guild: int,
        action: TemporaryActionSchema,
        now: datetime,
        no_reason: str,
    ) -> None:
        """Handle ban-type temporary actions."""
        if action.id is None:
            return

        action_id = int(action.id)
        expires_at = cls._ensure_timezone_aware(action.expires_at)

        # Handle expired ban immediately
        if expires_at and expires_at <= now:
            logger.debug(f"Ban expired for user {action.user_id}, unbanning immediately")
            try:
                await client.rest.unban_member(guild, action.user_id, reason=no_reason)
                await TemporaryActionService.delete_temporary_action(action_id)
            except hikari.NotFoundError:
                logger.info(f"User {action.user_id} already unbanned or not found")
                await TemporaryActionService.delete_temporary_action(action_id)
            except Exception as e:
                logger.error(f"Error unbanning user {action.user_id}: {e}")
            return

        # Schedule future unban
        if expires_at:
            delay = int((expires_at - now).total_seconds())
            logger.debug(f"Scheduling unban for user {action.user_id} in {delay} seconds")
            GlobalState.tasks.add_or_refresh_task(
                action.user_id,
                PunishmentType.BAN,
                client.task(lightbulb.uniformtrigger(seconds=delay), max_invocations=1)(
                    cls._create_ban_expiry_task(action_id, guild, action.user_id, no_reason)
                ),
            )

    @staticmethod
    def _create_ban_expiry_task(
        action_id: int, guild_id: int, user_id: int, reason: str
    ) -> Callable[[], Awaitable[None]]:
        """Create a ban expiry task."""

        async def ban_expiry_task() -> None:
            logger.debug(f"Executing scheduled unban for user {user_id}, action {action_id}")
            try:
                await GlobalState.bot.get_client().rest.unban_member(
                    guild_id, user_id, reason=reason
                )
                await TemporaryActionService.delete_temporary_action(action_id)
                GlobalState.tasks.remove_task(user_id, PunishmentType.BAN)
                logger.debug(f"Completed scheduled unban for user {user_id}")
            except hikari.NotFoundError:
                logger.info(f"User {user_id} already unbanned or not found")
                await TemporaryActionService.delete_temporary_action(action_id)
            except Exception as e:
                logger.error(f"Error in ban expiry task for user {user_id}: {e}")

        return ban_expiry_task

    @classmethod
    async def _handle_timeout_action(
        cls,
        client: lightbulb.Client,
        guild: int,
        action: TemporaryActionSchema,
        now: datetime,
        no_reason: str,
    ) -> None:
        """Handle timeout-type temporary actions."""
        if action.id is None:
            return

        action_id = int(action.id)
        expires_at = cls._ensure_timezone_aware(action.expires_at)
        refresh_at = cls._ensure_timezone_aware(action.refresh_at)

        # Handle expired timeout
        if expires_at and expires_at <= now:
            logger.debug(f"Timeout expired for user {action.user_id}, deleting action {action_id}")
            await TemporaryActionService.delete_temporary_action(action_id)
            return

        # Discord's max timeout duration (28 days in seconds)
        max_timeout: Final[int] = 2419200

        # Handle timeout refresh
        if refresh_at and expires_at and refresh_at < expires_at:
            await cls._handle_timeout_refresh(client, guild, action, action_id, now, no_reason)
        # Initialize refresh for long timeouts that don't have refresh_at set
        elif expires_at and refresh_at is None and (expires_at - now).total_seconds() > max_timeout:
            logger.debug(f"Setting up initial refresh for long timeout for user {action.user_id}")
            # Create a modified action with an initial refresh_at value
            modified_action = TemporaryActionSchema(
                id=action.id,
                user_id=action.user_id,
                punishment_type=action.punishment_type,
                expires_at=action.expires_at,
                refresh_at=now + timedelta(seconds=max_timeout),
            )
            await cls._handle_timeout_refresh(
                client, guild, modified_action, action_id, now, no_reason
            )
        # Schedule timeout removal
        elif expires_at:
            delay = int((expires_at - now).total_seconds())
            logger.debug(f"Scheduling timeout removal for user {action.user_id} in {delay} seconds")
            GlobalState.tasks.add_or_refresh_task(
                action.user_id,
                PunishmentType.TIMEOUT,
                client.task(lightbulb.uniformtrigger(seconds=delay), max_invocations=1)(
                    cls._create_timeout_expiry_task(action_id, guild, action.user_id, no_reason)
                ),
            )

    @staticmethod
    async def _handle_timeout_refresh(
        client: lightbulb.Client,
        guild: int,
        action: TemporaryActionSchema,
        action_id: int,
        now: datetime,
        no_reason: str,
    ) -> None:
        """Handle timeout refresh logic."""
        if action.refresh_at is None:
            logger.warning(
                f"Attempted to refresh timeout for user {action.user_id} with None refresh_at"
            )
            return

        expires_at = action.expires_at
        if expires_at is None:
            logger.warning(
                f"Attempted to refresh timeout for user {action.user_id} with None expires_at"
            )
            return

        # Ensure expires_at is timezone-aware
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        # Calculate time until expiration (not until refresh)
        time_until_expiry = int((expires_at - now).total_seconds())
        max_timeout: Final[int] = 2419200  # 28 days in seconds (Discord limit)

        try:
            # Apply the timeout (either max allowed or remaining time if less)
            timeout_duration = min(time_until_expiry, max_timeout)
            await client.rest.edit_member(
                guild,
                action.user_id,
                communication_disabled_until=now + timedelta(seconds=timeout_duration),
                reason=no_reason,
            )

            # Check if we'll need another refresh later
            if time_until_expiry > max_timeout:
                # Need another refresh after this one
                next_refresh = now + timedelta(seconds=max_timeout)
                logger.debug(
                    f"Scheduling next timeout refresh for user {action.user_id} at {next_refresh}"
                )
                await TemporaryActionService.create_or_update_temporary_action(
                    TemporaryActionSchema(
                        id=action_id,
                        user_id=action.user_id,
                        punishment_type=action.punishment_type,
                        expires_at=expires_at,
                        refresh_at=next_refresh,
                    )
                )
            else:
                # No further refresh needed
                logger.debug(
                    f"No further refreshes needed for user {action.user_id}, expires in {time_until_expiry} seconds"
                )
                await TemporaryActionService.create_or_update_temporary_action(
                    TemporaryActionSchema(
                        id=action_id,
                        user_id=action.user_id,
                        punishment_type=action.punishment_type,
                        expires_at=expires_at,
                        refresh_at=None,
                    )
                )
        except Exception as e:
            logger.error(f"Error refreshing timeout for user {action.user_id}: {e}")

    @staticmethod
    def _create_timeout_expiry_task(
        action_id: int, guild_id: int, user_id: int, reason: str
    ) -> Callable[[], Awaitable[None]]:
        """Create a timeout expiry task."""

        async def timeout_expiry_task() -> None:
            logger.debug(f"Executing timeout removal for user {user_id}, action {action_id}")
            try:
                await GlobalState.bot.get_client().rest.edit_member(
                    guild_id,
                    user_id,
                    communication_disabled_until=None,
                    reason=reason,
                )
                await TemporaryActionService.delete_temporary_action(action_id)
                GlobalState.tasks.remove_task(user_id, PunishmentType.TIMEOUT)
                logger.debug(f"Completed timeout removal for user {user_id}")
            except hikari.NotFoundError:
                logger.info(f"User {user_id} not found during timeout removal")
                await TemporaryActionService.delete_temporary_action(action_id)
            except Exception as e:
                logger.error(f"Error in timeout expiry task for user {user_id}: {e}")

        return timeout_expiry_task
