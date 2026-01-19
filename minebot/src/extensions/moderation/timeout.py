from datetime import datetime, timedelta, timezone
from typing import Final

import hikari
import lightbulb

from core import GlobalState
from database.schemas import PunishmentLogSchema, TemporaryActionSchema
from database.services import PunishmentLogService, TemporaryActionService
from helper import CommandHelper, MessageHelper, PunishmentHelper, TimeHelper, UserHelper
from model import CommandsKeys, MessageKeys, PunishmentSource, PunishmentType

# Helper that manages command configuration and localization
helper: CommandHelper = CommandHelper(CommandsKeys.TIMEOUT)
loader: lightbulb.Loader = helper.get_loader()

# Discord's maximum timeout duration (28 days in seconds)
MAX_TIMEOUT_DURATION: Final[int] = 2419200


@loader.command
class Timeout(
    lightbulb.SlashCommand,
    name="extensions.timeout.label",
    description="extensions.timeout.description",
    default_member_permissions=helper.get_permissions(),
    hooks=helper.generate_hooks(),
    contexts=[hikari.ApplicationContextType.GUILD],
    localize=True,
):
    user: hikari.User = lightbulb.user(
        "extensions.timeout.options.user.label",
        "extensions.timeout.options.user.description",
        localize=True,
    )

    duration: str = lightbulb.string(
        "extensions.timeout.options.duration.label",
        "extensions.timeout.options.duration.description",
        localize=True,
    )

    reason: str | None = lightbulb.string(
        "extensions.timeout.options.reason.label",
        "extensions.timeout.options.reason.description",
        localize=True,
        default=None,
    )

    async def _refresh_timeout_task(
        self,
        ctx: lightbulb.Context,
        target_member: hikari.Member,
        punishment: TemporaryActionSchema,
        refresh_time: datetime,
        reason_messages: tuple[str, str],
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

                # Make sure refresh_at is properly set
                updated_punishment = await TemporaryActionService.create_or_update_temporary_action(
                    TemporaryActionSchema(
                        id=punishment.id,
                        user_id=punishment.user_id,
                        punishment_type=PunishmentType.TIMEOUT,
                        expires_at=punishment.expires_at,
                        refresh_at=next_refresh,  # Ensure this is not None
                    )
                )

                # Still exceeds max timeout, apply max timeout and schedule another refresh
                await target_member.edit(
                    communication_disabled_until=next_refresh,
                    reason=reason_messages[1],
                )

                # Schedule next refresh task
                @ctx.client.task(
                    lightbulb.uniformtrigger(seconds=MAX_TIMEOUT_DURATION), max_invocations=1
                )
                async def next_refresh_timeout() -> None:
                    await self._refresh_timeout_task(
                        ctx, target_member, updated_punishment, next_refresh, reason_messages
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
                        refresh_at=None,  # Only set to None for final period
                    )
                )

                await target_member.edit(
                    communication_disabled_until=punishment.expires_at,
                    reason=reason_messages[1],
                )

                # Schedule the final cleanup task
                delay = int(remaining_seconds)

                @ctx.client.task(lightbulb.uniformtrigger(seconds=delay), max_invocations=1)
                async def timeout_expired() -> None:
                    assert punishment.id is not None
                    await TemporaryActionService.delete_temporary_action(punishment.id)
                    GlobalState.tasks.remove_task(target_member, PunishmentType.TIMEOUT)

    async def _handle_extended_timeout(
        self,
        ctx: lightbulb.Context,
        target_member: hikari.Member,
        now: datetime,
        expires_at: datetime,
        reason_messages: tuple[str, str],
    ) -> None:
        """Handle timeouts longer than Discord's maximum allowable duration."""
        # First apply the maximum timeout duration
        initial_timeout_end = now + timedelta(seconds=MAX_TIMEOUT_DURATION)

        # Create a temporary action to track this extended timeout
        punishment = await TemporaryActionService.create_or_update_temporary_action(
            TemporaryActionSchema(
                user_id=target_member.id,
                punishment_type=PunishmentType.TIMEOUT,
                expires_at=expires_at,
                refresh_at=initial_timeout_end,
            )
        )

        await target_member.edit(
            communication_disabled_until=initial_timeout_end, reason=reason_messages[1]
        )

        # Schedule a task to refresh the timeout when it's about to expire
        @ctx.client.task(lightbulb.uniformtrigger(seconds=MAX_TIMEOUT_DURATION), max_invocations=1)
        async def refresh_timeout() -> None:
            await self._refresh_timeout_task(
                ctx, target_member, punishment, initial_timeout_end, reason_messages
            )

    async def _apply_timeout(
        self,
        ctx: lightbulb.Context,
        target_member: hikari.Member,
        parsed_duration: timedelta,
        reason_messages: tuple[str, str],
    ) -> None:
        """Apply timeout to a member with the given duration."""
        assert ctx.member is not None

        now = datetime.now(timezone.utc)
        expires_at = now + parsed_duration

        # Log the timeout in the punishment database
        await PunishmentLogService.create_or_update_punishment_log(
            PunishmentLogSchema(
                user_id=target_member.id,
                punishment_type=PunishmentType.TIMEOUT,
                reason=reason_messages[1],
                staff_id=ctx.member.id,
                duration=int(parsed_duration.total_seconds()),
                expires_at=expires_at,
                source=PunishmentSource.DISCORD,
            )
        )

        # Apply timeout with handling for durations longer than Discord's maximum
        if parsed_duration.total_seconds() > MAX_TIMEOUT_DURATION:
            await self._handle_extended_timeout(
                ctx, target_member, now, expires_at, reason_messages
            )
        else:
            # Set timeout for the requested duration
            await target_member.edit(
                communication_disabled_until=expires_at, reason=reason_messages[1]
            )

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        target_member: hikari.Member | None = await UserHelper.fetch_member(self.user)

        assert ctx.member is not None
        assert target_member is not None

        # Check if user can be moderated
        if not PunishmentHelper.can_moderate(target_member, ctx.member):
            await MessageHelper(
                MessageKeys.error.CAN_NOT_MODERATE,
                locale=ctx.interaction.locale,
                discord_username=target_member.username,
                discord_user_id=str(target_member.id),
                discord_user_mention=target_member.mention,
                discord_staff_username=ctx.member.username,
                discord_staff_user_id=str(ctx.member.id),
                discord_staff_user_mention=ctx.member.mention,
            ).send_response(ctx, ephemeral=True)
            return

        # Check if user is already timed out
        if target_member.communication_disabled_until() is not None:
            await MessageHelper(
                MessageKeys.error.USER_ALREADY_TIMED_OUT,
                locale=ctx.interaction.locale,
                discord_username=target_member.username,
                discord_user_id=str(target_member.id),
                discord_user_mention=target_member.mention,
            ).send_response(ctx, ephemeral=True)
            return

        # Parse duration and get reason
        parsed_duration = TimeHelper(ctx.interaction.locale).parse_time_string(self.duration)
        reason_messages = PunishmentHelper.get_reason(self.reason, ctx.interaction.locale)

        # Apply timeout
        await self._apply_timeout(ctx, target_member, parsed_duration, reason_messages)

        # Send success message
        await MessageHelper(
            MessageKeys.commands.TIMEOUT_USER_SUCCESS,
            locale=ctx.interaction.locale,
            discord_username=target_member.username,
            discord_user_id=str(target_member.id),
            discord_user_mention=target_member.mention,
            discord_staff_username=ctx.member.username,
            discord_staff_user_id=str(ctx.member.id),
            discord_staff_user_mention=ctx.member.mention,
            duration=TimeHelper(ctx.interaction.locale).from_timedelta(parsed_duration),
            reason=reason_messages[0],
        ).send_response(ctx, ephemeral=True)
