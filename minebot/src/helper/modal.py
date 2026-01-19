from logging import Logger
from typing import Callable

import hikari
from lightbulb.components.modals import Modal, TextInput

from debug import get_logger
from model.schemas import TextInputField

logger: Logger = get_logger(__name__)


class ModalHelper:
    """
    Helper class for creating and managing modal components in the Discord bot.

    This class provides utility methods for constructing form fields and
    handling modal interactions with standardized logging and error handling.
    """

    @staticmethod
    def get_field(
        instance: Modal, key: TextInputField, min_lenght: int = 0, max_length: int = 4000
    ) -> TextInput:
        """
        Creates a text input field for a modal based on the provided configuration.

        This method dynamically selects the appropriate input type (short text or paragraph)
        based on the style specified in the TextInputField key.

        Args:
            instance: The Modal instance to add the field to
            key: Configuration for the text input field (style, label, placeholder, value)
            min_lenght: Minimum allowed input length (default: 0)
            max_length: Maximum allowed input length (default: 4000)

        Returns:
            The created TextInput field that was added to the modal

        Raises:
            KeyError: If an invalid style is provided in the TextInputField
        """
        logger.debug(f"Creating field with label '{key.label}' and style '{key.style}'")

        mapper: dict[str, Callable] = {
            "SHORT": instance.add_short_text_input,
            "PARAGRAPH": instance.add_paragraph_text_input,
        }

        if key.style not in mapper:
            logger.error(f"Invalid input style '{key.style}' provided for field '{key.label}'")
            raise KeyError(f"Invalid input style: {key.style}")

        # Set undefined values properly for hikari
        placeholder: str | hikari.UndefinedType = key.placeholder or hikari.UNDEFINED
        value: str | hikari.UndefinedType = key.value or hikari.UNDEFINED

        logger.debug(
            f"Adding field '{key.label}' with min_length={min_lenght}, max_length={max_length}"
        )

        field = mapper[key.style](
            label=key.label,
            placeholder=placeholder,
            value=value,
            min_length=min_lenght,
            max_length=max_length,
        )

        logger.debug(f"Field '{key.label}' successfully added to modal")
        return field
