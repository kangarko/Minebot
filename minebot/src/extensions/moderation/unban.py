from typing import Sequence

import hikari
import lightbulb

from database.schemas import PunishmentLogSchema
from database.services import PunishmentLogService
from helper import CommandHelper, MessageHelper, PunishmentHelper
from model import CommandsKeys, MessageKeys, PunishmentSource, PunishmentType, SecretKeys
from settings import Settings

# Helper that manages command configuration and localization
helper: CommandHelper = CommandHelper(CommandsKeys.UNBAN)
loader: lightbulb.Loader = helper.get_loader()


async def autocomplete_callback(ctx: lightbulb.AutocompleteContext[str]) -> None:
    """Provide username autocompletion suggestions from the server's ban list."""
    assert ctx.interaction.guild_id is not None

    current_value = ctx.focused.value.lower() if isinstance(ctx.focused.value, str) else ""
    ban_list = await ctx.client.rest.fetch_bans(ctx.interaction.guild_id)

    # Filter banned users by partial username match
    value_to_recommend = []
    for ban in ban_list:
        username = ban.user.username
        if username and current_value in username.lower():
            value_to_recommend.append(username)
            if len(value_to_recommend) >= 25:  # Discord limits autocompletion options
                break

    await ctx.respond(value_to_recommend)


@loader.command
class UnBan(
    lightbulb.SlashCommand,
    name="extensions.unban.label",
    description="extensions.unban.description",
    default_member_permissions=helper.get_permissions(),
    hooks=helper.generate_hooks(),
    contexts=[hikari.ApplicationContextType.GUILD],
    localize=True,
):
    # Username parameter definition for the unban command target
    user: str = lightbulb.string(
        "extensions.unban.options.user.label",
        "extensions.unban.options.user.description",
        autocomplete=autocomplete_callback,  # Use autocomplete to find banned users
        localize=True,
    )

    # Optional reason for the unban action
    reason: str | None = lightbulb.string(
        "extensions.unban.options.reason.label",
        "extensions.unban.options.reason.description",
        localize=True,
        default=None,
    )

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        # Verify guild context exists for unban operation
        assert ctx.guild_id is not None
        assert ctx.member is not None

        # Find the banned user by username from the server's ban list
        username_to_check = self.user.lower()
        ban_list: Sequence[hikari.GuildBan] = await ctx.client.rest.fetch_bans(ctx.guild_id)

        target_user = next(
            (ban.user for ban in ban_list if ban.user.username.lower() == username_to_check), None
        )

        # Handle case where user isn't found in the ban list
        if not target_user:
            await MessageHelper(
                key=MessageKeys.error.USER_NOT_FOUND,
                locale=ctx.interaction.locale,
                discord_user_id="N/A",
                discord_username=username_to_check,
            ).send_response(ctx, ephemeral=True)
            return

        # Generate appropriate reason text for logging and notifications
        reason_messages = PunishmentHelper.get_reason(self.reason, ctx.interaction.locale)

        # Record unban action in moderation history database
        await PunishmentLogService.create_or_update_punishment_log(
            PunishmentLogSchema(
                user_id=target_user.id,
                punishment_type=PunishmentType.UNBAN,
                reason=reason_messages[1],
                staff_id=ctx.member.id,
                source=PunishmentSource.DISCORD,
            )
        )

        # Apply the unban through Discord API with moderator reason
        await ctx.client.rest.unban_user(
            Settings.get(SecretKeys.DEFAULT_GUILD), target_user, reason=reason_messages[1]
        )

        # Notify moderator of successful unban action
        await MessageHelper(
            MessageKeys.commands.UNBAN_USER_SUCCESS,
            locale=ctx.interaction.locale,
            discord_username=target_user.username,
            discord_user_id=str(target_user.id),
            discord_user_mention=target_user.mention,
            reason=reason_messages[0],  # User-facing reason
        ).send_response(ctx)
