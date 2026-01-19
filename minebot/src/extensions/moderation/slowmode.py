from datetime import timedelta

import hikari
import lightbulb

from helper import ChannelHelper, CommandHelper, MessageHelper, PunishmentHelper, TimeHelper
from model import CommandsKeys, MessageKeys

# Helper that manages command configuration and localization
helper: CommandHelper = CommandHelper(CommandsKeys.SLOWMODE)
loader: lightbulb.Loader = helper.get_loader()


@loader.command
class Slowmode(
    lightbulb.SlashCommand,
    name="extensions.slowmode.label",
    description="extensions.slowmode.description",
    default_member_permissions=helper.get_permissions(),
    hooks=helper.generate_hooks(),
    contexts=[hikari.ApplicationContextType.GUILD],
    localize=True,
):
    # Duration parameter specifies the slowmode duration
    duration: str = lightbulb.string(
        "extensions.slowmode.options.duration.label",
        "extensions.slowmode.options.duration.description",
        localize=True,
    )

    # Channel parameter allows moderators to specify which channel to set slowmode on
    # If omitted, defaults to the current channel where command is executed
    channel: hikari.PartialChannel | None = lightbulb.channel(
        "extensions.slowmode.options.channel.label",
        "extensions.slowmode.options.channel.description",
        channel_types=[hikari.ChannelType.GUILD_TEXT],
        default=None,
        localize=True,
    )

    # Optional reason for audit logs and notifications
    reason: str | None = lightbulb.string(
        "extensions.slowmode.options.reason.label",
        "extensions.slowmode.options.reason.description",
        default=None,
        localize=True,
    )

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        # Verify guild context exists for permission operations
        assert ctx.guild_id is not None

        # Use specified channel or default to the current interaction channel
        channel = self.channel or await ChannelHelper.fetch_channel(ctx.channel_id)

        # Process reason parameter for notifications and audit logs
        reason_messages = PunishmentHelper.get_reason(self.reason, ctx.interaction.locale)

        # Validate that target is a text channel where slowmode is possible
        if not isinstance(channel, hikari.GuildTextChannel):
            await MessageHelper(
                MessageKeys.error.CHANNEL_NOT_FOUND, ctx.interaction.locale
            ).send_response(ctx, ephemeral=True)
            return

        # Parse duration string into timedelta object
        duration = TimeHelper(ctx.interaction.locale).parse_time_string(self.duration)

        # Ensure the duration is within allowed bounds (0 to 6 hours)
        if duration > timedelta(hours=6):
            min_duration = TimeHelper(ctx.interaction.locale).from_timedelta(timedelta(seconds=0))
            max_duration = TimeHelper(ctx.interaction.locale).from_timedelta(timedelta(hours=6))
            await MessageHelper(
                MessageKeys.error.DURATION_OUT_OF_RANGE,
                ctx.interaction.locale,
                min_duration=min_duration,
                max_duration=max_duration,
            ).send_response(ctx, ephemeral=True)
            return

        # Set slowmode on the channel with the specified duration
        await channel.edit(rate_limit_per_user=duration, reason=reason_messages[1])

        # Prepare common parameters for notification messages
        common_params = {
            "channel_name": channel.name,
            "channel_id": channel.id,
            "channel_mention": channel.mention,
            "duration": TimeHelper(ctx.interaction.locale).from_timedelta(duration),
        }

        # Notify moderator of successful action (visible only to them)
        await MessageHelper(
            MessageKeys.commands.SLOWMODE_USER_SUCCESS,
            ctx.interaction.locale,
            **common_params,
            reason=reason_messages[0],  # User-facing reason
        ).send_response(ctx, ephemeral=True)

        # Log action to designated logging channel for moderation transparency
        await MessageHelper(
            MessageKeys.commands.SLOWMODE_LOG_SUCCESS,
            ctx.interaction.locale,
            **common_params,
            discord_staff_username=ctx.user.username,
            discord_staff_user_id=ctx.user.id,
            discord_staff_user_mention=ctx.user.mention,
            reason=reason_messages[1],  # Staff/audit log reason
        ).send_to_log_channel(helper)
