import hikari
import lightbulb

from database.schemas import PunishmentLogSchema
from database.services import PunishmentLogService
from helper import CommandHelper, MessageHelper, PunishmentHelper, UserHelper
from model import CommandsKeys, MessageKeys, PunishmentSource, PunishmentType

# Helper that manages command configuration and localization
helper: CommandHelper = CommandHelper(CommandsKeys.KICK)
loader: lightbulb.Loader = helper.get_loader()


@loader.command
class Kick(
    lightbulb.SlashCommand,
    name="extensions.kick.label",
    description="extensions.kick.description",
    default_member_permissions=helper.get_permissions(),
    hooks=helper.generate_hooks(),
    contexts=[hikari.ApplicationContextType.GUILD],
    localize=True,
):
    # User parameter identifies the target member to be kicked from the server
    user: hikari.User = lightbulb.user(
        "extensions.kick.options.user.label",
        "extensions.kick.options.user.description",
        localize=True,
    )

    # Optional reason for the kick that will be recorded in audit logs
    # and displayed in notifications
    reason: str | None = lightbulb.string(
        "extensions.kick.options.reason.label",
        "extensions.kick.options.reason.description",
        default=None,
        localize=True,
    )

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        assert ctx.member is not None

        # Retrieve complete member information for the kick target
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

        # Process reason parameter for both user-facing messages and audit logs
        reason_messages = PunishmentHelper.get_reason(self.reason, ctx.interaction.locale)

        # Record the punishment in the database for tracking and reporting
        await PunishmentLogService.create_or_update_punishment_log(
            PunishmentLogSchema(
                user_id=target_member.id,
                punishment_type=PunishmentType.KICK,
                reason=reason_messages[1],  # Store the detailed reason
                staff_id=ctx.user.id,  # Track which staff member performed the action
                source=PunishmentSource.DISCORD,  # Indicate source of punishment
            )
        )

        # Execute the actual kick operation with the reason for audit logs
        await target_member.kick(reason=reason_messages[1])

        # Notify the moderator that the kick was successful
        # Ephemeral response ensures only the command user sees the confirmation
        await MessageHelper(
            MessageKeys.commands.KICK_USER_SUCCESS,
            ctx.interaction.locale,
            discord_username=target_member.username,
            discord_user_id=str(target_member.id),
            discord_user_mention=target_member.mention,
            reason=reason_messages[0],  # User-facing reason
        ).send_response(ctx, ephemeral=True)
