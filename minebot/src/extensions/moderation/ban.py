from datetime import datetime, timedelta, timezone

import hikari
import lightbulb

from core import GlobalState
from database.schemas import PunishmentLogSchema, TemporaryActionSchema
from database.services import PunishmentLogService, TemporaryActionService
from helper import CommandHelper, MessageHelper, PunishmentHelper, TimeHelper, UserHelper
from model import CommandsKeys, MessageKeys, PunishmentSource, PunishmentType

# Helper that manages command configuration and localization
helper = CommandHelper(CommandsKeys.BAN)
loader: lightbulb.Loader = helper.get_loader()


@loader.command
class Ban(
    lightbulb.SlashCommand,
    name="extensions.ban.label",
    description="extensions.ban.description",
    default_member_permissions=helper.get_permissions(),
    hooks=helper.generate_hooks(),
    contexts=[hikari.ApplicationContextType.GUILD],
    localize=True,
):
    # User parameter definition for the ban command target
    user: hikari.User = lightbulb.user(
        "extensions.ban.options.user.label",
        "extensions.ban.options.user.description",
        localize=True,
    )

    duration: str | None = lightbulb.string(
        "extensions.ban.options.duration.label",
        "extensions.ban.options.duration.description",
        localize=True,
        default=None,
    )

    reason: str | None = lightbulb.string(
        "extensions.ban.options.reason.label",
        "extensions.ban.options.reason.description",
        localize=True,
        default=None,
    )

    async def _handle_temporary_ban(
        self,
        ctx: lightbulb.Context,
        target_member: hikari.Member,
        parsed_duration: timedelta,
    ) -> None:
        """Handle the creation and scheduling of a temporary ban."""
        # Persist temporary ban information to database with expiration
        expires_at = datetime.now(timezone.utc) + parsed_duration
        temporary_action = await TemporaryActionService.create_or_update_temporary_action(
            TemporaryActionSchema(
                user_id=target_member.id,
                punishment_type=PunishmentType.BAN,
                expires_at=expires_at,
            )
        )

        # Register timed task to automatically unban when duration expires
        @ctx.client.task(
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
                # Record error details for debugging and monitoring
                print(f"Error in temporary ban handler: {e}")

        GlobalState.tasks.add_or_refresh_task(
            target_member, PunishmentType.BAN, handle_temporary_ban
        )

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        # Verify guild context exists for ban operation
        assert ctx.guild_id is not None
        assert ctx.member is not None

        # Retrieve complete member information for the ban target
        target_member = await UserHelper.fetch_member(self.user)
        if not target_member:
            await MessageHelper(
                MessageKeys.error.MEMBER_NOT_FOUND, locale=ctx.interaction.locale
            ).send_response(ctx, ephemeral=True)
            return

        # Verify permission hierarchy allows this moderation action
        if not PunishmentHelper.can_moderate(target_member, ctx.member):
            await MessageHelper(
                MessageKeys.error.CAN_NOT_MODERATE, locale=ctx.interaction.locale
            ).send_response(ctx, ephemeral=True)
            return

        # Setup timing variables for temporary ban processing
        parsed_duration = timedelta(0)
        formatted_duration = None
        expiry = None

        # Process duration parameter if specified by moderator
        if self.duration:
            time_helper = TimeHelper(ctx.interaction.locale)
            parsed_duration = time_helper.parse_time_string(self.duration)

            # Configure temporary ban only for valid positive durations
            if parsed_duration.total_seconds() > 0:
                formatted_duration = time_helper.from_timedelta(parsed_duration)
                expiry = datetime.now(timezone.utc) + parsed_duration

        # Generate appropriate reason text for logging and notifications
        reason_messages = PunishmentHelper.get_reason(self.reason, ctx.interaction.locale)

        # Set up automatic unban for temporary bans
        if self.duration and parsed_duration.total_seconds() > 0:
            await self._handle_temporary_ban(ctx, target_member, parsed_duration)

        # Record punishment details in moderation history database
        duration_seconds = (
            int(parsed_duration.total_seconds()) if parsed_duration.total_seconds() > 0 else None
        )
        await PunishmentLogService.create_or_update_punishment_log(
            PunishmentLogSchema(
                user_id=target_member.id,
                punishment_type=PunishmentType.BAN,
                reason=reason_messages[1],
                staff_id=ctx.member.id,
                duration=duration_seconds,
                expires_at=expiry,  # Will be None for permanent bans
                source=PunishmentSource.DISCORD,
            )
        )

        # Apply the ban through Discord API with moderator reason
        await target_member.ban(reason=reason_messages[1])

        # Notify moderator of successful action with duration details
        if formatted_duration is None and self.duration:
            # Initialize time formatter if not already available
            time_helper = (
                TimeHelper(ctx.interaction.locale) if "time_helper" not in locals() else time_helper
            )
            formatted_duration = time_helper.from_timedelta(parsed_duration)

        await MessageHelper(
            MessageKeys.commands.BAN_USER_SUCCESS,
            locale=ctx.interaction.locale,
            discord_username=target_member.username,
            discord_user_id=str(target_member.id),
            discord_user_mention=target_member.mention,
            duration=formatted_duration,  # Empty string if None
            reason=reason_messages[0],  # User-facing reason
        ).send_response(ctx, ephemeral=True)
