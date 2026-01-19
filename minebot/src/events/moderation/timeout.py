from datetime import datetime, timedelta, timezone
from typing import cast

import hikari
import lightbulb

from core import GlobalState
from database.schemas import PunishmentLogSchema, TemporaryActionSchema
from database.services import PunishmentLogService, TemporaryActionService, UserService
from helper import CommandHelper, MessageHelper, PunishmentHelper, TimeHelper, UserHelper
from model import CommandsKeys, MessageKeys, PunishmentSource, PunishmentType
from websocket import WebSocketManager
from websocket.schemas.event import CommandExecutedSchema

# Helper that manages event configuration and localization
helper: CommandHelper = CommandHelper(CommandsKeys.TIMEOUT)
loader: lightbulb.Loader = helper.get_loader()


@loader.listener(hikari.AuditLogEntryCreateEvent)
async def on_member_update(event: hikari.AuditLogEntryCreateEvent) -> None:
    """
    Handles timeout events from Discord audit logs by creating punishment entries
    and sending log messages as needed.
    """
    # --- Early validation checks ---
    # Skip if no target user or not a member update event
    if (target_id := event.entry.target_id) is None:
        return

    if event.entry.action_type != hikari.AuditLogEventType.MEMBER_UPDATE:
        return

    # Ensure this is a timeout-related member update
    if not event.entry.changes or event.entry.changes[0].key != "communication_disabled_until":
        return

    # Check if a timeout was applied (not removed)
    if (communication_disabled_until := event.entry.changes[0].new_value) is None:
        return

    # Staff member who performed the action
    if (staff_id := event.entry.user_id) is None:
        return

    communication_disabled_until = cast(datetime, communication_disabled_until)

    # --- Check if that the refresh timeout ---
    temp_punishment = await TemporaryActionService.get_filtered_temporoary_action_logs(
        user_id=target_id, punishment_type=PunishmentType.TIMEOUT, get_latest=True
    )

    if temp_punishment:
        assert isinstance(temp_punishment, TemporaryActionSchema)

        # Convert event timestamp to UTC datetime for comparison
        event_time = datetime.fromtimestamp(event.entry.id.created_at.timestamp(), tz=timezone.utc)
        punishment_time = temp_punishment.created_at.replace(tzinfo=timezone.utc)
        time_diff = (event_time - punishment_time).total_seconds()

        # If the punishment was created earlier (than 120 seconds), consider it as a renewal
        if abs(time_diff) > 120:
            return

    # --- Check for duplicate entries ---
    # Get the most recent timeout for this user
    punishment = await PunishmentLogService.get_filtered_punishment_logs(
        user_id=target_id, punishment_type=PunishmentType.TIMEOUT, get_latest=True
    )

    # Check if the punishment is recent enough to correspond to this timeout event
    # or if we need to create a new punishment log
    create_new_entry = True

    if punishment:
        assert isinstance(punishment, PunishmentLogSchema)

        # Convert event timestamp to UTC datetime for comparison
        event_time = datetime.fromtimestamp(event.entry.id.created_at.timestamp(), tz=timezone.utc)
        punishment_time = punishment.created_at.replace(tzinfo=timezone.utc)
        time_diff = (event_time - punishment_time).total_seconds()

        # If the punishment was created recently (within 120 seconds), consider it the same timeout
        if abs(time_diff) < 120:
            create_new_entry = False

    # --- Create new punishment entry if needed ---
    if create_new_entry:
        # Process reason from audit log
        reason_messages = PunishmentHelper.get_reason(event.entry.reason, None)

        # Calculate timeout duration in seconds
        duration_seconds = int(
            (communication_disabled_until - datetime.now(timezone.utc)).total_seconds()
        )

        # Create punishment log entry
        punishment = await PunishmentLogService.create_or_update_punishment_log(
            PunishmentLogSchema(
                user_id=target_id,
                punishment_type=PunishmentType.TIMEOUT,
                reason=reason_messages[1],
                staff_id=staff_id,
                duration=duration_seconds,
                expires_at=communication_disabled_until,
                source=PunishmentSource.DISCORD,
            )
        )

    # Safety check - don't proceed if no punishment record exists
    if not punishment:
        return

    # Ensure the punishment is a valid schema instance
    assert isinstance(punishment, PunishmentLogSchema)

    if punishment.duration is None:
        # Invalid punishment entry without duration
        return

    # --- Synchronize punishment with server if enabled ---
    if GlobalState.commands.is_discord_to_minecraft(PunishmentType.TIMEOUT):
        user_data = await UserService.get_user(target_id)
        if not user_data or not user_data.minecraft_username:
            return

        await WebSocketManager.send_message(
            CommandExecutedSchema(
                server="all",
                command_type=PunishmentType.TIMEOUT,
                executor="MineBot",
                args={
                    "target": user_data.minecraft_username,
                    "duration": f"{punishment.duration}s",
                    "reason": punishment.reason,
                },
            )
        )

    # --- Fetch user information for logging ---
    target_member = await UserHelper.fetch_member(target_id)
    staff_member = await UserHelper.fetch_member(punishment.staff_id)

    if target_member is None or staff_member is None:
        return

    # --- Send log message ---
    await MessageHelper(
        MessageKeys.commands.TIMEOUT_LOG_SUCCESS,
        discord_username=target_member.username,
        discord_user_id=str(target_member.id),
        discord_user_mention=target_member.mention,
        discord_staff_username=staff_member.username,
        discord_staff_user_id=str(staff_member.id),
        discord_staff_user_mention=staff_member.mention,
        duration=TimeHelper().from_timedelta(timedelta(seconds=punishment.duration)),
        reason=punishment.reason,  # Staff-facing/detailed reason
    ).send_to_log_channel(helper)
