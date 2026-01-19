from datetime import datetime, timedelta, timezone

import hikari
import lightbulb

from helper import CommandHelper, MessageHelper, PunishmentHelper
from model import CommandsKeys, MessageKeys

# Helper that manages command configuration and localization
helper: CommandHelper = CommandHelper(CommandsKeys.CLEAR)
loader: lightbulb.Loader = helper.get_loader()


@loader.command
class Clear(
    lightbulb.SlashCommand,
    name="extensions.clear.label",
    description="extensions.clear.description",
    default_member_permissions=helper.get_permissions(),
    hooks=helper.generate_hooks(),
    contexts=[hikari.ApplicationContextType.GUILD],
    localize=True,
):
    # Amount parameter for specifying how many messages to delete
    amount: int = lightbulb.integer(
        "extensions.clear.options.amount.label",
        "extensions.clear.options.amount.description",
        localize=True,
    )

    # Optional reason for audit logs and moderation records
    reason: str | None = lightbulb.string(
        "extensions.clear.options.reason.label",
        "extensions.clear.options.reason.description",
        default=None,
        localize=True,
    )

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        # Generate formatted reason messages for user feedback and logs
        reason_messages = PunishmentHelper.get_reason(self.reason, ctx.interaction.locale)

        # Calculate bulk delete limit (Discord API restriction: can't delete messages older than 14 days)
        bulk_delete_limit = datetime.now(timezone.utc) - timedelta(days=14)

        # Create message iterator with appropriate filters:
        # - Messages must be newer than 14 days old (Discord API limitation)
        # - Messages must be older than the current time (avoid potential race conditions)
        # - Limit to the requested amount of messages
        iterator = (
            ctx.client.rest.fetch_messages(ctx.channel_id)
            .take_while(lambda m: m.created_at > bulk_delete_limit)
            .filter(lambda m: m.created_at < datetime.now(timezone.utc))
            .limit(self.amount)
        )

        # Convert iterator to a list of messages to be deleted
        messages_to_delete = await iterator.collect(list)

        # Common parameters for feedback messages to avoid repetition
        common_params = {
            "channel_name": ctx.interaction.channel.name,
            "channel_id": ctx.channel_id,
            "channel_mention": ctx.interaction.channel.mention,
            "amount": len(messages_to_delete),  # Get actual count of messages to be deleted
        }

        # Execute the bulk deletion operation with audit log reason
        await ctx.client.rest.delete_messages(
            ctx.channel_id, messages_to_delete, reason=reason_messages[1]
        )

        # Send confirmation message to the moderator with deletion details
        await MessageHelper(
            MessageKeys.commands.CLEAR_USER_SUCCESS,
            ctx.interaction.locale,
            reason=reason_messages[0],  # User-facing reason
            **common_params,
        ).send_response(ctx, ephemeral=True)

        # Send notification to moderation log channel for accountability
        await MessageHelper(
            MessageKeys.commands.CLEAR_LOG_SUCCESS,
            ctx.interaction.locale,
            discord_staff_username=ctx.user.username,
            discord_staff_user_id=ctx.user.id,
            discord_staff_user_mention=ctx.user.mention,
            reason=reason_messages[1],  # Audit log reason
            **common_params,
        ).send_to_log_channel(helper)
