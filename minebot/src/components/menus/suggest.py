import asyncio
import uuid

from lightbulb.components.menus import Menu, MenuContext

from components.modals.suggest import SuggestResponseModal
from helper import MenuHelper, MessageHelper
from model import MenuKeys, MessageKeys
from model.schemas import SuggestConfirmationButtons
from settings import Localization


class SuggestConfirmMenu(Menu):
    def __init__(self) -> None:
        menu_data: SuggestConfirmationButtons = Localization.get(MenuKeys.SUGGEST_CONFIRMATION)

        MenuHelper.get_button(
            self, menu_data.approve, on_press=self.on_approve, custom_id="suggestion_approve"
        )
        MenuHelper.get_button(
            self, menu_data.reject, on_press=self.on_reject, custom_id="suggestion_reject"
        )

    async def on_approve(self, ctx: MenuContext) -> None:
        modal = SuggestResponseModal(
            ctx.interaction.locale,
            ctx.interaction.message.id,
            "approved",
        )

        await ctx.respond_with_modal(modal.title, c_id := str(uuid.uuid4()), components=modal)
        try:
            await modal.attach(ctx.client, c_id, timeout=600)
        except asyncio.TimeoutError:
            await MessageHelper(
                MessageKeys.error.TIMEOUT, locale=ctx.interaction.locale
            ).send_response(ctx, ephemeral=True)

    async def on_reject(self, ctx: MenuContext) -> None:
        modal = SuggestResponseModal(
            ctx.interaction.locale,
            ctx.interaction.message.id,
            "rejected",
        )

        await ctx.respond_with_modal(modal.title, c_id := str(uuid.uuid4()), components=modal)
        try:
            await modal.attach(ctx.client, c_id, timeout=600)
        except asyncio.TimeoutError:
            await MessageHelper(
                MessageKeys.error.TIMEOUT, locale=ctx.interaction.locale
            ).send_response(ctx, ephemeral=True)
