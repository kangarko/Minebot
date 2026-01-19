from datetime import datetime, timezone

import hikari
import lightbulb

from core import GlobalState
from database.schemas import PunishmentLogSchema, TemporaryActionSchema
from database.services import PunishmentLogService, TemporaryActionService, UserService
from helper import CommandHelper, MessageHelper, PunishmentHelper, UserHelper
from model import CommandsKeys, MessageKeys, PunishmentSource, PunishmentType
from websocket import WebSocketManager
from websocket.schemas.event import CommandExecutedSchema

helper: CommandHelper = CommandHelper(CommandsKeys.UNBAN)
loader: lightbulb.Loader = helper.get_loader()


@loader.listener(hikari.AuditLogEntryCreateEvent)
async def on_ban_delete(event: hikari.AuditLogEntryCreateEvent) -> None:
    """
    Handles unban events from Discord audit logs by cleaning up temporary actions,
    creating punishment entries, and sending log messages as needed.
    """
    # --- Early validation checks ---
    # Skip if no target user or not a ban event
    if (target_id := event.entry.target_id) is None:
        return

    if event.entry.action_type != hikari.AuditLogEventType.MEMBER_BAN_REMOVE:
        return

    if (staff_id := event.entry.user_id) is None:
        return

    # --- Clean up temporary ban records ---
    temp_punishment = await TemporaryActionService.get_filtered_temporoary_action_logs(
        user_id=target_id, punishment_type=PunishmentType.BAN, get_latest=True
    )

    if temp_punishment:
        assert isinstance(temp_punishment, TemporaryActionSchema)
        assert temp_punishment.id is not None
        await TemporaryActionService.delete_temporary_action(temp_punishment.id)
        GlobalState.tasks.cancel_task(target_id, PunishmentType.BAN)

    # --- Check for duplicate entries ---
    create_new_entry = True

    # Convert event timestamp to UTC datetime
    event_time = datetime.fromtimestamp(event.entry.id.created_at.timestamp(), tz=timezone.utc)

    punishment = await PunishmentLogService.get_filtered_punishment_logs(
        user_id=target_id, punishment_type=PunishmentType.UNBAN, get_latest=True
    )

    if punishment:
        assert isinstance(punishment, PunishmentLogSchema)

        punishment_time = punishment.created_at.replace(tzinfo=timezone.utc)
        time_diff = abs((event_time - punishment_time).total_seconds())

        # If a recent punishment log exists, don't create a new one
        if time_diff < 120:
            create_new_entry = False

    # --- Create new punishment entry if needed ---
    reason_messages = PunishmentHelper.get_reason(event.entry.reason, None)

    if create_new_entry:
        # This is likely a ban performed outside the bot's commands
        punishment = await PunishmentLogService.create_or_update_punishment_log(
            PunishmentLogSchema(
                user_id=target_id,
                punishment_type=PunishmentType.UNBAN,
                reason=reason_messages[1],
                staff_id=staff_id,
                source=PunishmentSource.DISCORD,
            )
        )

    if not punishment:
        return

    # Ensure the punishment is a valid schema instance
    assert isinstance(punishment, PunishmentLogSchema)

    # --- Synchronize punishment with server if enabled ---
    if GlobalState.commands.is_discord_to_minecraft(PunishmentType.UNBAN):
        user_data = await UserService.get_user(target_id)
        if not user_data or not user_data.minecraft_username:
            return

        await WebSocketManager.send_message(
            CommandExecutedSchema(
                server="all",
                command_type=PunishmentType.UNBAN,
                executor="MineBot",
                args={
                    "target": user_data.minecraft_username,
                    "reason": punishment.reason,
                },
            )
        )

    # --- Fetch user information for logging ---
    target_member = await UserHelper.fetch_user(target_id)
    staff_member = await UserHelper.fetch_user(punishment.staff_id)

    if target_member is None or staff_member is None:
        return

    # --- Send log message ---
    await MessageHelper(
        MessageKeys.commands.UNBAN_LOG_SUCCESS,
        discord_username=target_member.username,
        discord_user_id=str(target_member.id),
        discord_user_mention=target_member.mention,
        discord_staff_username=staff_member.username,
        discord_staff_user_id=str(staff_member.id),
        discord_staff_user_mention=staff_member.mention,
        reason=punishment.reason,
    ).send_to_log_channel(helper)
