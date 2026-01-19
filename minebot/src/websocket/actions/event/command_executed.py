from datetime import datetime, timedelta, timezone
from logging import Logger
from typing import Awaitable, Callable, Final, TypeVar

import hikari
import lightbulb

from core import GlobalState
from database.schemas import PunishmentLogSchema, TemporaryActionSchema
from database.services import PunishmentLogService, TemporaryActionService, UserService
from debug import get_logger
from helper import MessageHelper, PunishmentHelper, TimeHelper, UserHelper
from model import MessageKeys, PunishmentSource, PunishmentType, SecretKeys
from settings import Settings

from ...action_registry import websocket_action
from ...schemas.event import CommandExecutedSchema

logger: Logger = get_logger(__name__)

# Discord's maximum timeout duration (28 days in seconds)
MAX_TIMEOUT_DURATION: Final[int] = 2419200
T = TypeVar("T")


async def safe_execute(
    func: Callable[..., Awaitable[T]], error_msg: str, *args, **kwargs
) -> T | None:
    """Execute a function safely with standardized error handling."""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        logger.error(f"{error_msg}: {e}")
        return None


async def fetch_member_safe(user: hikari.User) -> hikari.Member | None:
    """Safely fetch a guild member from a user object with error handling."""
    member = await safe_execute(
        UserHelper.fetch_member, f"Error fetching member for user {user.id}", user
    )

    if member is None:
        logger.warning(f"Could not fetch member for user {user.id}")

    return member


async def log_punishment(
    user_id: int,
    punishment_type: PunishmentType | str,
    reason: str,
    staff_id: int,
    source: PunishmentSource,
    duration: int | None = None,
    expires_at: datetime | None = None,
) -> None:
    """Create a punishment log entry with consistent parameters."""
    await PunishmentLogService.create_or_update_punishment_log(
        PunishmentLogSchema(
            user_id=user_id,
            punishment_type=punishment_type,
            reason=reason,
            staff_id=staff_id,
            duration=duration,
            expires_at=expires_at,
            source=source,
        )
    )


async def _refresh_timeout_task(
    client: lightbulb.Client,
    target_member: hikari.Member,
    punishment: TemporaryActionSchema,
    refresh_time: datetime,
    reason: str,
) -> None:
    """Task to refresh a timeout that needs to be extended beyond Discord's maximum duration."""
    assert punishment.id is not None
    assert punishment.expires_at is not None

    now = datetime.now(timezone.utc)

    # Check if we still need to keep the timeout active
    if refresh_time < punishment.expires_at:
        remaining_seconds = (punishment.expires_at - refresh_time).total_seconds()

        if remaining_seconds > MAX_TIMEOUT_DURATION:
            next_refresh = now + timedelta(seconds=MAX_TIMEOUT_DURATION)

            updated_punishment = await TemporaryActionService.create_or_update_temporary_action(
                TemporaryActionSchema(
                    id=punishment.id,
                    user_id=punishment.user_id,
                    punishment_type=PunishmentType.TIMEOUT,
                    expires_at=punishment.expires_at,
                    refresh_at=next_refresh,
                )
            )

            await target_member.edit(
                communication_disabled_until=next_refresh,
                reason=reason,
            )

            # Schedule next refresh task
            @client.task(lightbulb.uniformtrigger(seconds=MAX_TIMEOUT_DURATION), max_invocations=1)
            async def next_refresh_timeout() -> None:
                await _refresh_timeout_task(
                    client, target_member, updated_punishment, next_refresh, reason
                )

            GlobalState.tasks.add_or_refresh_task(
                target_member, PunishmentType.TIMEOUT, next_refresh_timeout
            )
        else:
            # Final timeout period is less than max, set exact expiry time
            await TemporaryActionService.create_or_update_temporary_action(
                TemporaryActionSchema(
                    id=punishment.id,
                    user_id=punishment.user_id,
                    punishment_type=PunishmentType.TIMEOUT,
                    expires_at=punishment.expires_at,
                    refresh_at=None,
                )
            )

            await target_member.edit(
                communication_disabled_until=punishment.expires_at,
                reason=reason,
            )

            # Schedule the final cleanup task
            delay = int(remaining_seconds)

            @client.task(lightbulb.uniformtrigger(seconds=delay), max_invocations=1)
            async def timeout_expired() -> None:
                assert punishment.id is not None
                await TemporaryActionService.delete_temporary_action(punishment.id)
                GlobalState.tasks.remove_task(target_member, PunishmentType.TIMEOUT)

            GlobalState.tasks.add_or_refresh_task(
                target_member, PunishmentType.TIMEOUT, timeout_expired
            )


async def _handle_extended_timeout(
    client: lightbulb.Client,
    target_member: hikari.Member,
    now: datetime,
    expires_at: datetime,
    reason: str,
) -> None:
    """Handle timeouts longer than Discord's maximum allowable duration."""
    initial_timeout_end = now + timedelta(seconds=MAX_TIMEOUT_DURATION)

    punishment = await TemporaryActionService.create_or_update_temporary_action(
        TemporaryActionSchema(
            user_id=target_member.id,
            punishment_type=PunishmentType.TIMEOUT,
            expires_at=expires_at,
            refresh_at=initial_timeout_end,
        )
    )

    await target_member.edit(communication_disabled_until=initial_timeout_end, reason=reason)

    @client.task(lightbulb.uniformtrigger(seconds=MAX_TIMEOUT_DURATION), max_invocations=1)
    async def refresh_timeout() -> None:
        await _refresh_timeout_task(client, target_member, punishment, initial_timeout_end, reason)

    GlobalState.tasks.add_or_refresh_task(target_member, PunishmentType.TIMEOUT, refresh_timeout)


async def _apply_timeout(
    client: lightbulb.Client,
    executor: hikari.User,
    target_member: hikari.Member,
    parsed_duration: timedelta,
    reason: str,
) -> None:
    """Apply timeout to a member with the given duration."""
    now = datetime.now(timezone.utc)
    expires_at = now + parsed_duration

    # Log the timeout in the punishment database
    await log_punishment(
        user_id=target_member.id,
        punishment_type=PunishmentType.TIMEOUT,
        reason=reason,
        staff_id=executor.id,
        duration=int(parsed_duration.total_seconds()),
        expires_at=expires_at,
        source=PunishmentSource.DISCORD,
    )

    # Apply timeout with handling for durations longer than Discord's maximum
    if parsed_duration.total_seconds() > MAX_TIMEOUT_DURATION:
        await _handle_extended_timeout(client, target_member, now, expires_at, reason)
    else:
        # Set timeout for the requested duration
        await target_member.edit(communication_disabled_until=expires_at, reason=reason)


async def _handle_kick(executor: hikari.User, target: hikari.User, reason: str) -> None:
    """Kick a user from the Discord server.

    Args:
        executor: The user executing the kick
        target: The user to be kicked
        reason: The reason for the kick
    """
    target_member = await fetch_member_safe(target)
    if not target_member:
        logger.warning(f"Cannot kick user {target.username} - not found in guild")
        return

    await log_punishment(
        user_id=target_member.id,
        punishment_type=PunishmentType.KICK,
        reason=reason,
        staff_id=executor.id,
        source=PunishmentSource.MINECRAFT,
    )

    # Execute the kick operation
    await safe_execute(target_member.kick, f"Error kicking user {target.id}", reason=reason)


async def _handle_ban(executor: hikari.User, target: hikari.User, reason: str) -> None:
    target_member = await fetch_member_safe(target)
    if not target_member:
        return

    await log_punishment(
        user_id=target_member.id,
        punishment_type=PunishmentType.BAN,
        reason=reason,
        staff_id=executor.id,
        source=PunishmentSource.MINECRAFT,
    )

    await safe_execute(target_member.ban, f"Error banning user {target.id}", reason=reason)


async def _handle_tempban(
    executor: hikari.User, target: hikari.User, duration: str, reason: str, client: lightbulb.Client
) -> None:
    target_member = await fetch_member_safe(target)
    if not target_member:
        return

    parsed_duration = TimeHelper(hikari.Locale.EN_US).parse_time_string(duration)
    if parsed_duration.total_seconds() < 0:
        return

    expires_at = datetime.now(timezone.utc) + parsed_duration

    temporary_action = await TemporaryActionService.create_or_update_temporary_action(
        TemporaryActionSchema(
            user_id=target_member.id,
            punishment_type=PunishmentType.BAN,
            expires_at=expires_at,
        )
    )

    @client.task(
        lightbulb.uniformtrigger(seconds=int(parsed_duration.total_seconds())),
        max_invocations=1,
    )
    async def handle_temporary_ban() -> None:
        try:
            # Remove the ban when time period completes
            await target_member.unban(
                reason=MessageHelper(key=MessageKeys.general.NO_REASON)._decode_plain()
            )

            # Remove temporary action record from database after completion
            if temporary_action.id is not None:
                await TemporaryActionService.delete_temporary_action(temporary_action.id)

            # Remove the task from global state to prevent re-execution
            GlobalState.tasks.remove_task(target_member, PunishmentType.BAN)
        except Exception as e:
            logger.error(f"Error in temporary ban handler: {e}")

    GlobalState.tasks.add_or_refresh_task(target_member, PunishmentType.BAN, handle_temporary_ban)

    await log_punishment(
        user_id=target_member.id,
        punishment_type=PunishmentType.BAN,
        reason=reason,
        staff_id=executor.id,
        duration=int(parsed_duration.total_seconds()),
        expires_at=expires_at,
        source=PunishmentSource.MINECRAFT,
    )

    await safe_execute(
        target_member.ban, f"Error applying temporary ban to user {target.id}", reason=reason
    )


async def _handle_unban(
    executor: hikari.User, target: hikari.User, reason: str, client: lightbulb.Client
) -> None:
    default_guild = Settings.get(SecretKeys.DEFAULT_GUILD)

    ban_list = await safe_execute(client.rest.fetch_bans, "Error fetching ban list", default_guild)

    if not ban_list:
        return

    target_user = next(
        (ban.user for ban in ban_list if ban.user.username.lower() == target.username.lower()), None
    )

    if not target_user:
        logger.warning(f"User {target.username} is not banned")
        return

    await log_punishment(
        user_id=target_user.id,
        punishment_type=PunishmentType.UNBAN,
        reason=reason,
        staff_id=executor.id,
        source=PunishmentSource.MINECRAFT,
    )

    await safe_execute(
        client.rest.unban_user,
        f"Error unbanning user {target_user.id}",
        default_guild,
        target_user,
        reason=reason,
    )


async def _handle_timeout(
    executor: hikari.User,
    target: hikari.User,
    duration: str,
    reason: str,
    client: lightbulb.Client,
) -> None:
    target_member = await fetch_member_safe(target)
    if not target_member:
        return

    parsed_duration = TimeHelper(hikari.Locale.EN_US).parse_time_string(duration)

    if parsed_duration.total_seconds() < 0:
        return

    await _apply_timeout(client, executor, target_member, parsed_duration, reason)


async def _handle_untimeout(executor: hikari.User, target: hikari.User, reason: str) -> None:
    target_member = await fetch_member_safe(target)
    if not target_member:
        return

    await log_punishment(
        user_id=target_member.id,
        punishment_type=PunishmentType.UNTIMEOUT,
        reason=reason,
        staff_id=executor.id,
        source=PunishmentSource.MINECRAFT,
    )

    await safe_execute(
        target_member.edit,
        f"Error removing timeout for user {target.id}",
        communication_disabled_until=None,
        reason=reason,
    )


async def _fetch_discord_user(minecraft_username: str | None) -> hikari.User | None:
    """Fetch Discord user from Minecraft username."""
    if not minecraft_username:
        return None

    user_data = await UserService.get_user_by_minecraft_username(minecraft_username)
    if not user_data:
        return None

    return await UserHelper.fetch_user(user_data.id)


# Command handler mapping for cleaner dispatch
COMMAND_HANDLERS = {
    PunishmentType.KICK: _handle_kick,
    PunishmentType.BAN: _handle_ban,
    "tempban": _handle_tempban,
    PunishmentType.UNBAN: _handle_unban,
    PunishmentType.TIMEOUT: _handle_timeout,
    PunishmentType.UNTIMEOUT: _handle_untimeout,
}


@websocket_action("command-executed", CommandExecutedSchema)
async def command_executed(data: CommandExecutedSchema, client: lightbulb.Client) -> None:
    # Check command sync permission - tempban uses BAN permission
    command_type_for_check = (
        PunishmentType.BAN if data.command_type == "tempban" else data.command_type
    )
    if not GlobalState.commands.is_minecraft_to_discord(command_type_for_check):
        return

    # Extract data - safely handle potentially missing arguments
    args = data.args or {}
    raw_executor = data.executor
    raw_target = args.get("target")
    duration = args.get("duration")
    reason = PunishmentHelper.get_reason(args.get("reason"), None)[0]

    # Fetch executor
    executor = await _fetch_discord_user(raw_executor)
    if not executor:
        logger.warning(f"Could not resolve Discord user for Minecraft username: {raw_executor}")
        return

    if not raw_target:
        logger.warning("No target specified for command execution")
        return

    # Fetch target only for commands that need it
    target = await _fetch_discord_user(raw_target)
    if not target:
        logger.warning(f"Could not resolve Discord user for Minecraft username: {raw_target}")
        return

    # Look up the handler function for this command type
    handler = COMMAND_HANDLERS.get(data.command_type)
    if not handler:
        logger.warning(f"Unhandled command type: {data.command_type}")
        return

    # Execute the appropriate handler with consistent error handling
    try:
        if data.command_type == "tempban":
            if not duration:
                logger.warning("Duration missing for tempban command")
                return
            await handler(executor, target, duration, reason, client)
        elif data.command_type == PunishmentType.TIMEOUT:
            if not duration:
                logger.warning("Duration missing for timeout command")
                return
            await handler(executor, target, duration, reason, client)
        elif data.command_type == PunishmentType.UNBAN:
            await handler(executor, target, reason, client)
        else:
            await handler(executor, target, reason)
    except Exception as e:
        logger.error(f"Error handling command {data.command_type}: {e}")
