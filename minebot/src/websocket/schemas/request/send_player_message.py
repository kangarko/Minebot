from pydantic import Field, model_validator

from model import MessageType

from ..base import BaseSchema, ResponseAwaitableSchema


class SendPlayerMessageSchema(BaseSchema, ResponseAwaitableSchema, action="send-player-message"):
    """Schema for the send-player-message action."""

    message_type: MessageType
    message: str
    username: str | None = Field(default=None, max_length=16)
    uuid: str | None = Field(default=None, max_length=36)

    @model_validator(mode="after")
    def validate_username_or_uuid(self) -> "SendPlayerMessageSchema":
        if self.username is None and self.uuid is None:
            raise ValueError("Either 'username' or 'uuid' must be provided.")
        return self
