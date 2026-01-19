import asyncio
import uuid
from typing import Sequence

import hikari
from lightbulb.components.menus import Menu, MenuContext, TextSelectOption

from components.modals.ticket import TicketInputModal
from database.services.ticket_channel import TicketChannelService
from helper import MenuHelper, MessageHelper
from helper.ticket import TicketHelper
from model import MenuKeys, MessageKeys
from settings import Localization


class BaseTicketMenu(Menu):
    """Base class for ticket menus with common functionality."""

    @property
    def ticket_helper(self) -> type[TicketHelper]:
        from helper import TicketHelper

        return TicketHelper

    def __init__(self) -> None:
        if not self.ticket_helper._system_enabled:
            raise ValueError("Ticket system is currently disabled")
        super().__init__()

    async def handle_modal_interaction(self, ctx: MenuContext, category_str: str) -> None:
        """Handle modal creation, response, and timeout for ticket interactions."""

        if self.ticket_helper._max_ticket_per_user is None:
            return

        if (
            len(await TicketChannelService.get_ticket_channels_by_owner(ctx.user.id))
            >= self.ticket_helper._max_ticket_per_user
        ):
            await MessageHelper(
                MessageKeys.error.MAX_AMOUNT_OF_TICKETS_REACHED,
                locale=ctx.interaction.locale,
                max_tickets=self.ticket_helper._max_ticket_per_user,
            ).send_response(ctx, ephemeral=True)
            return

        category_data = self.ticket_helper._categories.get(category_str)

        if not category_data:
            raise ValueError(f"Category '{category_str}' not found in ticket categories.")

        modal = TicketInputModal(category_str, category_data, ctx.interaction.locale)
        modal_id = str(uuid.uuid4())

        await ctx.respond_with_modal(modal.title, modal_id, components=modal)
        try:
            await modal.attach(ctx.client, modal_id, timeout=600)  # 10 minutes timeout
        except asyncio.TimeoutError:
            await MessageHelper(
                MessageKeys.error.TIMEOUT, locale=ctx.interaction.locale
            ).send_response(ctx, ephemeral=True)


class TicketDropdownMenu(BaseTicketMenu):
    def __init__(self) -> None:
        super().__init__()
        categories = self.ticket_helper._categories

        options: Sequence[TextSelectOption] = []
        for label, category in categories.items():
            options.append(
                TextSelectOption(
                    label=category.category_name,
                    value=label,
                    description=category.category_description or hikari.UNDEFINED,
                    emoji=category.category_emoji or hikari.UNDEFINED,
                )
            )

        self.select = self.add_text_select(
            options, self.on_select, custom_id="ticket-category-select"
        )

    async def on_select(self, ctx: MenuContext) -> None:
        category_str = ctx.selected_values_for(self.select)[0]
        await self.handle_modal_interaction(ctx, category_str)


class TicketButtonMenu(BaseTicketMenu):
    def __init__(self) -> None:
        super().__init__()
        categories = self.ticket_helper._categories

        for label, category in categories.items():
            if not category.category_button_style:
                raise ValueError(
                    f"Button style for category '{label}' is not defined in ticket categories."
                )

            self.add_interactive_button(
                getattr(hikari.ButtonStyle, category.category_button_style),
                self.on_click,
                custom_id=label,
                label=category.category_name,
                emoji=category.category_emoji or hikari.UNDEFINED,
            )

    async def on_click(self, ctx: MenuContext) -> None:
        category_str = ctx.component.custom_id
        await self.handle_modal_interaction(ctx, category_str)


class TicketInnerMenu(BaseTicketMenu):
    def __init__(self) -> None:
        super().__init__()

        MenuHelper.get_button(
            self,
            Localization.get(MenuKeys.TICKET_CLOSE),
            self.on_close,
            custom_id="ticker-close-button",
        )

    async def on_close(self, ctx: MenuContext) -> None:
        menu = TickerOuterMenu(ctx.interaction.message.id)
        await MessageHelper(
            MessageKeys.systems.TICKET_SYSTEM_CLOSING, locale=ctx.interaction.locale
        ).send_response(ctx, ephemeral=True, components=menu)
        try:
            await menu.attach(ctx.client, timeout=60)  # 1 minute timeout
        except asyncio.TimeoutError:
            await ctx.interaction.delete_initial_response()


class TickerOuterMenu(BaseTicketMenu):
    def __init__(self, message_id: int) -> None:
        super().__init__()

        MenuHelper.get_button(self, Localization.get(MenuKeys.TICKET_CONFIRM), self.on_confirm)
        MenuHelper.get_button(self, Localization.get(MenuKeys.TICKET_CANCEL), self.on_cancel)

        self.message_id = message_id

    async def on_confirm(self, ctx: MenuContext) -> None:
        await ctx.client.rest.edit_message(
            ctx.interaction.channel_id, self.message_id, components=[]
        )
        await self.ticket_helper.close_ticket_channel(ctx.interaction.channel_id)

    async def on_cancel(self, ctx: MenuContext) -> None:
        await ctx.client.rest.edit_message(
            ctx.interaction.channel_id, self.message_id, components=TicketInnerMenu()
        )
