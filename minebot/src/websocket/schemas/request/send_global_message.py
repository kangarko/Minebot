from model import MessageType

from ..base import BaseSchema


class SendGlobalMessageSchema(BaseSchema, action="send-global-message"):
    """Schema for the send-global-message action."""

    message_type: MessageType
    message: str
