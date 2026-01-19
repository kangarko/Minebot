from logging import Logger
from typing import Any, Literal, Sequence, cast, overload

import hikari
import lightbulb

from debug import get_logger
from helper import ChannelHelper, CommandHelper, EventHelper
from model import (
    CommandMessageKeys,
    DiscordEmbed,
    DiscordMessage,
    ErrorMessageKeys,
    EventMessageKeys,
    GeneralMessageKeys,
    TextMessage,
)
from model.message import SystemMessageKeys
from settings import Localization

# Set up logger for this module
logger: Logger = get_logger(__name__)

ContextType = (
    lightbulb.Context | lightbulb.components.MenuContext | lightbulb.components.ModalContext
)

# Replace DecodeType with more specific typing
MessagePairMode = Literal["text", "embed", "mixed"]

# Define the MessageKeyType as a union of all possible enum types
MessageKeyType = (
    CommandMessageKeys
    | ErrorMessageKeys
    | EventMessageKeys
    | GeneralMessageKeys
    | SystemMessageKeys
)


class MessageHelper:
    """
    A helper class for handling message localization and responses.

    This class provides functionality to retrieve, format, and send localized messages
    based on message keys and the specified locale. It can handle both plain text and
    embedded rich messages.

    Attributes:
        key (MessageKeyType): The key identifier for the message to be retrieved.
        locale (str | hikari.Locale | None): The locale for the message. If None,
            the default locale will be used.
        kwargs (dict[str, Any]): Format parameters to be substituted in the message.

    Methods:
        decode(): Retrieves and formats the message based on the key, locale, and kwargs.
        respond(ctx, ephemeral): Sends the formatted message as a response to the given context.
    """

    def __init__(
        self, key: MessageKeyType, locale: str | hikari.Locale | None = None, **kwargs
    ) -> None:
        """
        Initialize a new MessageHelper instance.

        This helper is used to manage localized messages for an application,
        allowing for messages to be retrieved by key and locale.

        Args:
            key (MessageKeyType): The message key to identify the message.
            locale (str | hikari.Locale | None, optional): The locale to use for the message.
                If None, the default locale will be used. Defaults to None.
            **kwargs: Additional arguments to format the message with.

        Note:
            The initialization is logged at debug level with the provided parameters.
        """
        self.key: MessageKeyType = key
        self.locale: str | hikari.Locale | None = locale
        self.kwargs: dict[str, Any] = kwargs
        logger.debug(f"[Message: {key.name}] Initialized with locale: {locale}, params: {kwargs}")

    def _decode_plain(self, content: TextMessage | None = None) -> str:
        """
        Decode a plain message into a formatted string.

        This method takes a TextMessage object, formats its text with the provided keyword arguments,
        and returns the resulting string. If no content is provided, it retrieves the message from
        the localization system using the current key and locale.

        Parameters:
            content (TextMessage | None): The message to decode. If None, retrieves message from localization.

        Returns:
            str: The formatted message text.

        Note:
            The method also logs a debug message with a truncated version of the result.
        """
        if content is None:
            content = cast(TextMessage, Localization.get(key=self.key, locale=self.locale))

        result: str = content.text.format(**self.kwargs) if content.text else ""
        truncated: str = result[:50] + ("..." if len(result) > 50 else "")
        logger.debug(f"[Message: {self.key.name}] Plain content: {truncated}")
        return result

    def _decode_embed(self, content: DiscordEmbed | None = None) -> hikari.Embed:
        """
        Decodes an DiscordEmbed object into a hikari.Embed.

        This method constructs a hikari.Embed object from the given DiscordEmbed,
        applying any format arguments from self.kwargs. If no content is provided,
        it fetches the content from localization using self.key and self.locale.

        Args:
            content (DiscordEmbed | None): The DiscordEmbed object to decode.
                If None, content will be fetched from localization. Defaults to None.

        Returns:
            hikari.Embed: A fully constructed hikari.Embed object with all relevant
                fields populated from the DiscordEmbed.

        Note:
            The method formats all string fields using self.kwargs if they exist.
        """
        if content is None:
            content = cast(DiscordEmbed, Localization.get(key=self.key, locale=self.locale))

        embed = hikari.Embed(
            title=content.title.format(**self.kwargs) if content.title else None,
            description=content.description.format(**self.kwargs) if content.description else None,
            url=str(content.url) if content.url else None,
            color=content.color.as_hex() if content.color else None,
            timestamp=content.timestamp,
        )

        # Add fields if they exist
        if content.fields:
            logger.debug(f"[Message: {self.key.name}] Adding {len(content.fields)} fields")
            for field in content.fields:
                embed.add_field(
                    name=field.name.format(**self.kwargs) if field.name else None,
                    value=field.value.format(**self.kwargs) if field.value else None,
                    inline=field.inline,
                )

        # Set footer if exists
        if content.footer:
            embed.set_footer(
                text=content.footer.text.format(**self.kwargs) if content.footer.text else "",
                icon=str(content.footer.icon) if content.footer.icon else None,
            )

        # Set image, thumbnail and author if they exist
        if content.image:
            embed.set_image(str(content.image))

        if content.thumbnail:
            embed.set_thumbnail(str(content.thumbnail))

        if content.author:
            embed.set_author(
                name=content.author.name.format(**self.kwargs) if content.author.name else None,
                url=str(content.author.url) if content.author.url else None,
                icon=str(content.author.icon) if content.author.icon else None,
            )

        logger.debug(f"[Message: {self.key.name}] Embed message construction completed")
        return embed

    def decode(self) -> str | hikari.Embed:
        """
        Decodes a message into either a plain string or a hikari.Embed object.

        This method retrieves a message schema from the localization system using the key and locale
        specified in the instance. It then formats the message content with the provided kwargs.

        If the message type is "plain", it returns a formatted string.
        If the message type is "embed", it constructs and returns a hikari.Embed object with all
        the specified properties (title, description, fields, footer, image, thumbnail, author).

        Returns:
            str | hikari.Embed: A formatted string for plain messages or a fully constructed
                               hikari.Embed object for embed messages.

        Logs:
            Debug information about the decoding process.
        """
        logger.debug(f"[Message: {self.key.name}] Decoding {self.locale} message")
        message: DiscordMessage = Localization.get(key=self.key, locale=self.locale)
        content: TextMessage | DiscordEmbed = message.content

        if message.message_type == "plain":
            content = cast(TextMessage, content)
            return self._decode_plain(content)

        # Must be an embed message
        logger.debug(f"[Message: {self.key.name}] Building embed message")
        content = cast(DiscordEmbed, content)
        return self._decode_embed(content)

    @overload
    def get_localized_message_pair(self, mode: Literal["text"]) -> tuple[str, str]: ...

    @overload
    def get_localized_message_pair(
        self, mode: Literal["embed"]
    ) -> tuple[hikari.Embed, hikari.Embed]: ...

    @overload
    def get_localized_message_pair(
        self, mode: Literal["mixed"]
    ) -> tuple[str | hikari.Embed, str | hikari.Embed]: ...

    def get_localized_message_pair(
        self, mode: MessagePairMode = "mixed"
    ) -> (
        tuple[str, str]
        | tuple[hikari.Embed, hikari.Embed]
        | tuple[str | hikari.Embed, str | hikari.Embed]
    ):
        """
        Creates a pair of messages: one in the user's preferred locale and one in the default locale.

        This method generates two versions of the same message using the current key and format parameters:
        1. First message using the currently set locale (user's preference)
        2. Second message using the system default locale

        Args:
            mode: The format mode for the message pair:
                - "text": Force both messages to be plain text
                - "embed": Force both messages to be embeds
                - "mixed": Let each message be its natural type (text or embed)

        Returns:
            A tuple containing:
                - First element: Message in user's preferred locale
                - Second element: Same message in system default locale

        Note:
            This method temporarily modifies the instance's locale attribute but restores
            it before returning.
        """
        # Store original locale to restore it later
        original_locale = self.locale

        try:
            # Choose decoder method based on mode
            if mode == "text":
                # Use plain text decoder for string pairs
                user_message = self._decode_plain()

                # Create message with default locale
                self.locale = None
                default_message = self._decode_plain()

                return (user_message, default_message)

            elif mode == "embed":
                # Use embed decoder for embed pairs
                user_message = self._decode_embed()

                # Create message with default locale
                self.locale = None
                default_message = self._decode_embed()

                return (user_message, default_message)

            else:  # mode == "mixed"
                # Default behavior using general decode method
                user_message = self.decode()

                # Create message with default locale
                self.locale = None
                default_message = self.decode()

                return (user_message, default_message)

        finally:
            # Restore the original locale to prevent side effects
            self.locale = original_locale

    async def send_response(
        self,
        ctx: ContextType,
        ephemeral: bool = False,
        components: Sequence[hikari.api.ComponentBuilder] | None = None,
        attachment: hikari.Resourceish | None = None,
    ) -> hikari.Message:
        """
        Responds to a context with a message.

        This method decodes the message and sends it as a response to the given context.
        The message can be either a plain text or an embed.

        Args:
            ctx: The context to respond to. Can be any context type that supports the respond method.
            ephemeral: Whether the response should be ephemeral (only visible to the command invoker).
                        Defaults to False.

        Raises:
            Any exceptions that might be raised by the context's respond method.
        """
        message: str | hikari.Embed = self.decode()
        message_type = "embed" if isinstance(message, hikari.Embed) else "plain"

        logger.debug(
            f"[Message: {self.key.name}] Responding with {message_type} message (ephemeral: {ephemeral})"
        )

        response_message: hikari.Message = cast(
            hikari.Message,
            await ctx.respond(
                content=message,
                ephemeral=ephemeral,
                components=components or hikari.UNDEFINED,
                attachment=attachment or hikari.UNDEFINED,
            ),
        )
        logger.debug(f"[Message: {self.key.name}] Response sent successfully")

        return response_message

    async def send_to_log_channel(
        self,
        helper: CommandHelper | EventHelper,
        components: Sequence[hikari.api.ComponentBuilder] | None = None,
        attachment: hikari.Resourceish | None = None,
    ) -> hikari.Message | None:
        """
        Sends the message to the configured log channel.

        This method checks if logging is enabled, retrieves the log channel ID,
        fetches the channel, and then sends the decoded message to it.

        Args:
            helper: The (CommandHelper | EventHelper) instance to check logging configuration.

        Returns:
            None: The method returns early if logging is disabled or no channel is configured.
        """
        logger.debug(f"[Message: {self.key.name}] Checking if logging is enabled")
        channel_id = helper.get_log_channel_id()
        if not channel_id:
            logger.debug(f"[Message: {self.key.name}] Logging is disabled, skipping")
            return None

        logger.debug(f"[Message: {self.key.name}] Fetching channel {channel_id}")
        channel: hikari.TextableGuildChannel = await ChannelHelper.fetch_channel(
            channel_id, hikari.TextableGuildChannel
        )

        message: str | hikari.Embed = self.decode()
        message_type = "embed" if isinstance(message, hikari.Embed) else "plain"
        logger.debug(f"[Message: {self.key.name}] Sending {message_type} message to log channel")

        response_message: hikari.Message = await channel.send(
            content=message,
            components=components or hikari.UNDEFINED,
            attachment=attachment or hikari.UNDEFINED,
        )
        logger.debug(f"[Message: {self.key.name}] Log message sent successfully")

        return response_message

    async def send_to_channel(
        self,
        channel: int | hikari.TextableChannel,
        components: Sequence[hikari.api.ComponentBuilder] | None = None,
        attachment: hikari.Resourceish | None = None,
    ) -> hikari.Message | None:
        """
        Sends the message to a specific channel.

        This method retrieves the channel by its ID or object, decodes the message,
        and sends it to the specified channel.

        Args:
            channel: The ID or object of the channel to send the message to.

        Returns:
            hikari.Message | None: The sent message or None if the channel is not found.
        """
        logger.debug(f"[Message: {self.key.name}] Sending message to channel {channel}")
        if isinstance(channel, int):
            channel = await ChannelHelper.fetch_channel(channel, hikari.TextableChannel)

        message: str | hikari.Embed = self.decode()
        message_type = "embed" if isinstance(message, hikari.Embed) else "plain"
        logger.debug(f"[Message: {self.key.name}] Sending {message_type} message to channel")

        response_message: hikari.Message = await channel.send(
            content=message,
            components=components or hikari.UNDEFINED,
            attachment=attachment or hikari.UNDEFINED,
        )
        logger.debug(f"[Message: {self.key.name}] Message sent successfully to channel")

        return response_message
