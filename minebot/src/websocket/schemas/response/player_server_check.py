from pydantic import Field, model_validator

from ..base import BaseSchema, ResponseAwaitableSchema


class PlayerServerCheckSchema(BaseSchema, ResponseAwaitableSchema, action="player-server-check"):
    """Schema for the player-server-check action."""

    username: str | None = Field(default=None, max_length=16)
    uuid: str | None = Field(default=None, max_length=36)
    server: str | None = Field(default=None)

    @model_validator(mode="after")
    def validate_username_or_uuid(self) -> "PlayerServerCheckSchema":
        if self.username is None and self.uuid is None:
            raise ValueError("Either 'username' or 'uuid' must be provided.")
        return self
