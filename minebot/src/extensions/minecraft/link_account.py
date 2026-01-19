import asyncio
import secrets
import uuid

import hikari
import lightbulb

from components.modals.link_account import LinkAccountConfirmModal
from helper import CommandHelper, MessageHelper, MinecraftHelper
from hooks.minecraft import verify_minecraft_account_link
from model import CommandsKeys, MessageKeys, MessageType

# Helper that manages command configuration and localization
helper: CommandHelper = CommandHelper(CommandsKeys.LINK_ACCOUNT)
loader: lightbulb.Loader = helper.get_loader()


@loader.command
class LinkAccount(
    lightbulb.SlashCommand,
    name="extensions.link_account.label",
    description="extensions.link_account.description",
    default_member_permissions=helper.get_permissions(),
    hooks=helper.generate_hooks(verify_minecraft_account_link(False)),
    contexts=[hikari.ApplicationContextType.GUILD],
    localize=True,
):
    # Command parameter: Minecraft username to link with Discord account
    username: str = lightbulb.string(
        "extensions.link_account.options.username.label",
        "extensions.link_account.options.username.description",
        localize=True,
    )

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        # Get user's locale for localized responses
        user_locale: str = ctx.interaction.locale
        # Generate a random uppercase hex code for verification
        code: str = secrets.token_hex(5).upper()  # 10 characters

        # Check if the player is online in Minecraft
        if not await MinecraftHelper.fetch_player_status(username=self.username):
            # Send error message if player isn't online
            await MessageHelper(
                key=MessageKeys.error.PLAYER_NOT_ONLINE,
                locale=user_locale,
                discord_username=ctx.user.username,
                discord_user_id=ctx.user.id,
                discord_user_mention=ctx.user.mention,
                minecraft_username=self.username,
                minecraft_uuid="None",
            ).send_response(ctx, ephemeral=True)
            return  # Exit if player is not online

        # Send verification code to the Minecraft player in-game
        await MinecraftHelper.send_player_message(
            message_type=MessageType.INFO,
            username=self.username,
            message=MessageHelper(
                key=MessageKeys.commands.LINK_ACCOUNT_MINECRAFT_CONFIRMATION_CODE,
                locale=user_locale,
                confirmation_code=code,
            )._decode_plain(),
        )

        # Get the player's Minecraft UUID for storing in the account link
        player_uuid: str | None = await MinecraftHelper.fetch_player_uuid(self.username)

        # Create the modal dialog for the user to enter the verification code
        modal = LinkAccountConfirmModal(
            username=self.username,
            uuid=player_uuid or "N/A",
            code=code,
            user_locale=ctx.interaction.locale,
            helper=helper,
        )

        # Display the modal and wait for user input
        # Generate a random ID for this specific modal instance
        await ctx.respond_with_modal(modal.title, c_id := str(uuid.uuid4()), components=modal)
        try:
            # Wait for the user to submit the modal
            await modal.attach(ctx.client, c_id)
        except asyncio.TimeoutError:
            # Handle case when user doesn't complete the modal in time
            await MessageHelper(MessageKeys.error.TIMEOUT).send_response(ctx, ephemeral=True)
