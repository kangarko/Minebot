import hikari
from lightbulb.components.modals import Modal, ModalContext, TextInput

from database.schemas import SuggestionSchema
from database.services import SuggestionService
from exceptions.command import CommandExecutionError
from helper import (
    ChannelHelper,
    MessageHelper,
    MinecraftHelper,
    ModalHelper,
)
from model import CommandsKeys, MessageKeys, ModalKeys
from model.message import CommandMessageKeys
from model.schemas import (
    SuggestCommandConfig,
    SuggestRespondModal,
    SuggestSendModal,
    UserReward,
)
from settings import Localization, Settings


class SuggestRequestModal(Modal):
    def __init__(self, user_locale: str) -> None:
        # Get localized modal data based on user's locale
        modal_data: SuggestSendModal = Localization.get(ModalKeys.SUGGEST_SEND, locale=user_locale)

        self.title: str = modal_data.title
        # Create the code input field with appropriate constraints
        self.input: TextInput = ModalHelper.get_field(
            instance=self, key=modal_data.fields.suggestion, min_lenght=10, max_length=4000
        )

        # Fetch command configuration for suggestions
        _command_data: SuggestCommandConfig = Settings.get(CommandsKeys.SUGGEST)
        self._pending_channel: int = _command_data.pending_channel

        # Store data as private attributes for later use
        self._user_locale: str = user_locale

    async def on_submit(self, ctx: ModalContext) -> None:
        suggestion: str = ctx.value_for(self.input) or "N/A"

        common_params: dict[str, str] = {
            "discord_username": ctx.user.username,
            "discord_user_id": str(ctx.user.id),
            "discord_user_mention": ctx.user.mention,
            "suggestion": suggestion,
        }

        try:
            from components.menus.suggest import SuggestConfirmMenu

            menu = SuggestConfirmMenu()

            await MessageHelper(
                key=MessageKeys.commands.SUGGEST_USER_SUCCESS,
                locale=self._user_locale,
                **common_params,
            ).send_response(ctx, ephemeral=True)

            pending_channel: hikari.TextableChannel = await ChannelHelper.fetch_channel(
                self._pending_channel, hikari.TextableChannel
            )

            pending_message: hikari.Message | None = await MessageHelper(
                key=MessageKeys.commands.SUGGEST_PENDING_SUCCESS, **common_params
            ).send_to_channel(pending_channel, components=menu)

            if pending_message:
                await SuggestionService.create_or_update_suggestion(
                    SuggestionSchema(
                        id=pending_message.id,
                        user_id=ctx.user.id,
                        suggestion=suggestion,
                        status="pending",
                    )
                )

        except Exception:
            await MessageHelper(
                key=MessageKeys.commands.SUGGEST_USER_FAILURE,
                locale=self._user_locale,
                **common_params,
            ).send_response(ctx, ephemeral=True)
            await MessageHelper(
                key=MessageKeys.commands.SUGGEST_PENDING_FAILURE, **common_params
            ).send_to_channel(pending_channel)


class SuggestResponseModal(Modal):
    def __init__(self, user_locale: str, message_id: int, respond_type: str) -> None:
        # Validate respond_type early
        valid_types = {"approved", "rejectd"}
        if respond_type not in valid_types:
            raise ValueError(f"Invalid respond_type. Must be one of: {', '.join(valid_types)}")

        # Get localized modal data based on user's locale
        modal_data: SuggestRespondModal = Localization.get(
            ModalKeys.SUGGEST_RESPOND, locale=user_locale
        )

        self.title: str = modal_data.title
        # Create the input field with appropriate constraints
        self.input: TextInput = ModalHelper.get_field(
            instance=self, key=modal_data.fields.response, min_lenght=10, max_length=4000
        )

        # Store data as private attributes for later use
        self._command_data: SuggestCommandConfig = Settings.get(CommandsKeys.SUGGEST)
        self._pending_channel: int = self._command_data.pending_channel
        self._result_channel: int = self._command_data.result_channel
        self._user_locale: str = user_locale
        self._message_id: int = message_id
        self._respond_type: str = respond_type
        # Cache message keys mapping for respond types
        self._message_key_map: dict[str, CommandMessageKeys] = {
            "approved": MessageKeys.commands.SUGGEST_RESULT_APPROVE,
            "rejected": MessageKeys.commands.SUGGEST_RESULT_REJECT,
        }

    async def give_rewards(self, ctx: ModalContext, user_id: int) -> None:
        """Give rewards to the user based on configuration."""
        rewards: UserReward | None = self._command_data.reward
        if not rewards:
            return

        await MinecraftHelper.add_rewards(ctx.user, rewards)

    async def on_submit(self, ctx: ModalContext) -> None:
        """Handle modal submission."""
        try:
            # Fetch suggestion data
            suggestion_data: SuggestionSchema | None = await SuggestionService.get_suggestion(
                self._message_id
            )

            if not suggestion_data:
                await MessageHelper(
                    key=MessageKeys.general.FAILURE, locale=self._user_locale
                ).send_response(ctx, ephemeral=True)
                return

            # Fetch user data
            user: hikari.User = await ctx.client.rest.fetch_user(suggestion_data.user_id)

            # Prepare common parameters for messages
            common_params: dict[str, str] = {
                "discord_username": user.username,
                "discord_user_id": str(user.id),
                "discord_user_mention": user.mention,
                "discord_staff_username": ctx.user.username,
                "discord_staff_user_id": str(ctx.user.id),
                "discord_staff_user_mention": ctx.user.mention,
                "reason": ctx.value_for(self.input) or "N/A",
                "suggestion": suggestion_data.suggestion,
            }

            # Get the appropriate message key for this response type
            message_key = self._message_key_map.get(self._respond_type)
            if not message_key:
                raise CommandExecutionError(f"Invalid respond type: {self._respond_type}")

            # Send response to result channel
            result_channel: hikari.TextableChannel = await ChannelHelper.fetch_channel(
                self._result_channel, hikari.TextableChannel
            )

            await ctx.client.rest.create_message(
                result_channel,
                MessageHelper(
                    key=message_key,
                    locale=self._user_locale,
                    **common_params,
                ).decode(),
            )

            # Update suggestion status in database
            await SuggestionService.create_or_update_suggestion(
                SuggestionSchema(
                    id=suggestion_data.id,
                    user_id=suggestion_data.user_id,
                    staff_id=ctx.user.id,
                    suggestion=suggestion_data.suggestion,
                    status=self._respond_type,
                )
            )

            # Give rewards if suggestion was approved
            if self._respond_type == "approved":
                await self.give_rewards(ctx, suggestion_data.user_id)

            # Send success response to user
            await MessageHelper(
                MessageKeys.general.SUCCESS, locale=self._user_locale
            ).send_response(ctx, ephemeral=True)

            # Fetch pending channel to remove buttons
            pending_channel: hikari.TextableChannel = await ChannelHelper.fetch_channel(
                self._pending_channel, hikari.TextableChannel
            )

            # Remove buttons from the original message
            await ctx.client.rest.edit_message(
                pending_channel,
                self._message_id,
                components=[],
            )

        except CommandExecutionError as e:
            # Handle specific command execution errors
            await MessageHelper(
                key=MessageKeys.general.FAILURE, locale=self._user_locale, error_message=str(e)
            ).send_response(ctx, ephemeral=True)
        except Exception:
            # Handle general errors
            await MessageHelper(
                key=MessageKeys.error.CHANNEL_NOT_FOUND, locale=self._user_locale
            ).send_response(ctx, ephemeral=True)
