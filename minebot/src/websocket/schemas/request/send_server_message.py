from model import MessageType

from ..base import ServerBaseSchema


class SendServerMessageSchema(ServerBaseSchema, action="send-server-message"):
    """Schema for the send-server-message action."""

    message_type: MessageType
    message: str
