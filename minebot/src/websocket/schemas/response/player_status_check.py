from pydantic import Field, model_validator

from ..base import BaseSchema, ResponseAwaitableSchema


class PlayerStatusCheckSchema(BaseSchema, ResponseAwaitableSchema, action="player-status-check"):
    """Schema for the player-status-check action."""

    username: str | None = Field(default=None, max_length=16)
    uuid: str | None = Field(default=None, max_length=36)
    online: bool | None = Field(default=None)

    @model_validator(mode="after")
    def validate_username_or_uuid(self) -> "PlayerStatusCheckSchema":
        if self.username is None and self.uuid is None:
            raise ValueError("Either 'username' or 'uuid' must be provided.")
        return self
