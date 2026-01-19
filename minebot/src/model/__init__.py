"""
Model package for Minebot, providing core data structures and enumerations.

This package defines essential models and enumerations used throughout the
application, ensuring consistency and reusability of key components.
"""

from .config import (
    BotKeys,
    CommandsKeys,
    DatabaseKeys,
    EventsKeys,
    SecretKeys,
    SystemsKeys,
    WebSocketKeys,
)
from .message import (
    CommandMessageKeys,
    ErrorMessageKeys,
    EventMessageKeys,
    GeneralMessageKeys,
    MenuKeys,
    MessageKeys,
    ModalKeys,
    TimeUnitKeys,
)
from .ready import (
    LogStyle,
    MessageType,
    PunishmentSource,
    PunishmentType,
    TicketCreationMethod,
    TicketCreationStyle,
    TicketTranscriptFormat,
    TicketTranscriptUploadMethod,
)
from .schemas import BotSettings, DiscordEmbed, DiscordMessage, LocalizationData, TextMessage

__all__: list[str] = [
    "BotKeys",
    "CommandsKeys",
    "DatabaseKeys",
    "EventsKeys",
    "SecretKeys",
    "SystemsKeys",
    "WebSocketKeys",
    "MessageKeys",
    "ModalKeys",
    "TimeUnitKeys",
    "CommandMessageKeys",
    "ErrorMessageKeys",
    "EventMessageKeys",
    "GeneralMessageKeys",
    "MenuKeys",
    "LogStyle",
    "MessageType",
    "PunishmentSource",
    "PunishmentType",
    "BotSettings",
    "DiscordEmbed",
    "DiscordMessage",
    "LocalizationData",
    "TextMessage",
    "TicketCreationMethod",
    "TicketCreationStyle",
    "TicketTranscriptFormat",
    "TicketTranscriptUploadMethod",
]
