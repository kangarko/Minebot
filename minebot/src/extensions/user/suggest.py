import asyncio
import uuid

import hikari
import lightbulb

from components.modals.suggest import SuggestRequestModal
from helper import CommandHelper
from helper.message import MessageHelper
from model import CommandsKeys
from model.message import MessageKeys

# Helper that manages command configuration and localization
helper: CommandHelper = CommandHelper(CommandsKeys.SUGGEST)
loader: lightbulb.Loader = helper.get_loader()


@loader.command
class Suggest(
    lightbulb.SlashCommand,
    name="extensions.suggest.label",
    description="extensions.suggest.description",
    default_member_permissions=helper.get_permissions(),
    hooks=helper.generate_hooks(),
    contexts=[hikari.ApplicationContextType.GUILD],
    localize=True,
):
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        # Create a modal for the suggestion with appropriate localization
        modal = SuggestRequestModal(ctx.interaction.locale)

        # Generate a unique ID for this modal instance
        c_id = str(uuid.uuid4())

        # Show the modal to the user
        await ctx.respond_with_modal(modal.title, c_id, components=modal)
        try:
            # Wait for the user to submit the modal
            await modal.attach(ctx.client, c_id)
        except asyncio.TimeoutError:
            # If the user doesn't submit the modal within the timeout period
            # Send an ephemeral error message that only the user can see
            await MessageHelper(MessageKeys.error.TIMEOUT).send_response(ctx, ephemeral=True)
