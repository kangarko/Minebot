from typing import cast

from lightbulb.components.modals import Modal, ModalContext, TextInput

from core import GlobalState
from helper import MessageHelper, ModalHelper
from model import DiscordEmbed, DiscordMessage, MessageKeys, ModalKeys, TextMessage
from model.schemas import (
    BasicTicketModal,
    ChannelTicketCategory,
    ThreadTicketCategory,
)
from settings import Localization


class TicketInputModal(Modal):
    def __init__(
        self,
        category_str: str,
        category_data: ChannelTicketCategory | ThreadTicketCategory,
        user_locale: str,
    ) -> None:
        from helper import TicketHelper

        if not TicketHelper._system_enabled:
            raise ValueError("Ticket system is currently disabled")

        self._bot = GlobalState.bot.get_bot()
        self.category_str: str = category_str
        self.category_data = category_data
        self.inputs: dict[str, TextInput] = {}

        # Get localized modal data based on user's locale
        modal_data: dict[str, BasicTicketModal] = Localization.get(
            ModalKeys.TICKET_MODALS, locale=user_locale
        )

        modal: BasicTicketModal | None = modal_data.get(category_str)
        if not modal:
            raise ValueError(f"Modal data for category '{category_str}' not found.")

        creations: dict[str, DiscordMessage] = Localization.get(
            MessageKeys.systems.TICKET_SYSTEM_CREATIONS, locale=user_locale
        )

        self.creation_message: DiscordMessage | None = creations.get(category_str)
        if not self.creation_message:
            raise ValueError(f"Creation message for category '{category_str}' not found.")

        self.title: str = modal.title

        # Create input fields
        for label, field in modal.fields.items():
            self.inputs[label] = ModalHelper.get_field(self, field)

    async def on_submit(self, ctx: ModalContext) -> None:
        from helper import TicketHelper

        # Collect input values with dict comprehension
        values: dict[str, str] = {
            f"ticket_{self.category_str}_{label}": ctx.value_for(input_field) or ""
            for label, input_field in self.inputs.items()
        }

        channel = await TicketHelper.create_ticket_channel(self.category_data, ctx.user)
        if not channel:
            return

        # Prepare common parameters
        common_params: dict[str, str] = {
            "ticket_owner_discord_username": ctx.user.username,
            "ticket_owner_discord_user_id": str(ctx.user.id),
            "ticket_owner_discord_user_mention": ctx.user.mention,
            "ticket_channel_name": channel.name or "N/A",
            "ticket_channel_id": str(channel.id),
            "ticket_channel_mention": channel.mention,
            "ticket_category": self.category_data.category_name,
        }

        # Merge all parameters for message creation
        all_params = {**values, **common_params}
        message_helper = MessageHelper(MessageKeys.systems.TICKET_SYSTEM_CREATIONS, **all_params)

        assert self.creation_message is not None

        if self.creation_message.message_type == "embed":
            message_content = message_helper._decode_embed(
                cast(DiscordEmbed, self.creation_message.content)
            )
        elif self.creation_message.message_type == "plain":
            message_content = message_helper._decode_plain(
                cast(TextMessage, self.creation_message.content)
            )
        else:
            raise ValueError(
                f"Unsupported message type: {self.creation_message.message_type}. "
                "Expected 'embed' or 'plain'."
            )

        # Import the TicketInnerMenu component
        from components.menus.ticket import TicketInnerMenu

        # Create message in channel
        await self._bot.rest.create_message(channel, message_content, components=TicketInnerMenu())

        # Send success response to user
        await MessageHelper(MessageKeys.systems.TICKET_USER_SUCCESS, **common_params).send_response(
            ctx, ephemeral=True
        )
