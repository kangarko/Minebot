import hikari
import lightbulb

from helper import ChannelHelper, CommandHelper, MessageHelper, PunishmentHelper
from model import CommandsKeys, MessageKeys

# Helper that manages command configuration and localization
helper: CommandHelper = CommandHelper(CommandsKeys.LOCK)
loader: lightbulb.Loader = helper.get_loader()


@loader.command
class Lock(
    lightbulb.SlashCommand,
    name="extensions.lock.label",
    description="extensions.lock.description",
    default_member_permissions=helper.get_permissions(),
    hooks=helper.generate_hooks(),
    contexts=[hikari.ApplicationContextType.GUILD],
    localize=True,
):
    # Channel parameter allows moderators to specify which channel to lock
    # If omitted, defaults to the current channel where command is executed
    channel: hikari.PartialChannel | None = lightbulb.channel(
        "extensions.lock.options.channel.label",
        "extensions.lock.options.channel.description",
        channel_types=[hikari.ChannelType.GUILD_TEXT],
        default=None,
        localize=True,
    )

    # Optional reason for audit logs and notifications
    reason: str | None = lightbulb.string(
        "extensions.lock.options.reason.label",
        "extensions.lock.options.reason.description",
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

        # Validate that target is a text channel where locking is possible
        if not isinstance(channel, hikari.GuildTextChannel):
            await MessageHelper(
                MessageKeys.error.CHANNEL_NOT_FOUND, ctx.interaction.locale
            ).send_response(ctx, ephemeral=True)
            return

        # Apply permission overwrite to disable message sending for @everyone role
        await channel.edit_overwrite(
            target=ctx.guild_id,  # Target is @everyone role (same ID as guild)
            target_type=hikari.PermissionOverwriteType.ROLE,
            deny=hikari.Permissions.SEND_MESSAGES,  # Remove message sending permission
            reason=reason_messages[1],  # Audit log reason
        )

        # Prepare common parameters for notification messages
        common_params = {
            "channel_name": channel.name,
            "channel_id": channel.id,
            "channel_mention": channel.mention,
        }

        # Notify moderator of successful action
        await MessageHelper(
            MessageKeys.commands.LOCK_USER_SUCCESS,
            ctx.interaction.locale,
            **common_params,
            reason=reason_messages[0],  # User-facing reason
        ).send_response(ctx, ephemeral=True)

        # Log action to designated logging channel for moderation transparency
        await MessageHelper(
            MessageKeys.commands.LOCK_LOG_SUCCESS,
            ctx.interaction.locale,
            **common_params,
            discord_staff_username=ctx.user.username,
            discord_staff_user_id=ctx.user.id,
            discord_staff_user_mention=ctx.user.mention,
            reason=reason_messages[1],  # Staff/audit log reason
        ).send_to_log_channel(helper)
