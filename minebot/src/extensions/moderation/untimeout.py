import hikari
import lightbulb

from database.schemas import PunishmentLogSchema
from database.services import PunishmentLogService
from helper import CommandHelper, MessageHelper, PunishmentHelper, UserHelper
from model import CommandsKeys, MessageKeys, PunishmentSource, PunishmentType

# Helper that manages command configuration and localization
helper: CommandHelper = CommandHelper(CommandsKeys.UNTIMEOUT)
loader: lightbulb.Loader = helper.get_loader()


@loader.command
class UnTimeout(
    lightbulb.SlashCommand,
    name="extensions.untimeout.label",
    description="extensions.untimeout.description",
    default_member_permissions=helper.get_permissions(),
    hooks=helper.generate_hooks(),
    contexts=[hikari.ApplicationContextType.GUILD],
    localize=True,
):
    # Command parameter to specify which user to remove timeout from
    user: hikari.User = lightbulb.user(
        "extensions.untimeout.options.user.label",
        "extensions.untimeout.options.user.description",
        localize=True,
    )

    # Optional reason for removing the timeout
    reason: str | None = lightbulb.string(
        "extensions.untimeout.options.reason.label",
        "extensions.untimeout.options.reason.description",
        localize=True,
        default=None,
    )

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        # Verify guild context exists for untimeout operation
        assert ctx.guild_id is not None
        assert ctx.member is not None

        # Fetch the target member from the guild
        target_member: hikari.Member | None = await UserHelper.fetch_member(self.user)
        if not target_member:
            await MessageHelper(
                MessageKeys.error.MEMBER_NOT_FOUND, locale=ctx.interaction.locale
            ).send_response(ctx, ephemeral=True)
            return

        # Check if the user currently has a timeout active
        if target_member.communication_disabled_until() is None:
            await MessageHelper(
                MessageKeys.error.USER_NOT_TIMED_OUT,
                locale=ctx.interaction.locale,
                discord_user_id=target_member.id,
                discord_username=target_member.username,
                discord_user_mention=target_member.mention,
            ).send_response(ctx, ephemeral=True)
            return

        # Get formatted reason messages for audit logs and response
        reason_messages = PunishmentHelper.get_reason(self.reason, ctx.interaction.locale)

        # Record untimeout action in moderation history database
        await PunishmentLogService.create_or_update_punishment_log(
            PunishmentLogSchema(
                user_id=target_member.id,
                punishment_type=PunishmentType.TIMEOUT,
                reason=reason_messages[1],
                staff_id=ctx.member.id,
                source=PunishmentSource.DISCORD,
            )
        )

        # Attempt to remove the timeout by setting communication_disabled_until to None
        await target_member.edit(communication_disabled_until=None, reason=reason_messages[1])

        # Notify about the successful removal of timeout
        await MessageHelper(
            MessageKeys.commands.UNTIMEOUT_USER_SUCCESS,
            locale=ctx.interaction.locale,
            discord_user_id=target_member.id,
            discord_username=target_member.username,
            discord_user_mention=target_member.mention,
            discord_staff_username=ctx.member.username,
            reason=reason_messages[0],
        ).send_response(ctx)
