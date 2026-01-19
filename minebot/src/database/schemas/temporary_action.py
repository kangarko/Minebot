from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, PositiveInt


class TemporaryActionSchema(BaseModel):
    id: PositiveInt | None = Field(default=None)
    user_id: PositiveInt
    punishment_type: str = Field(max_length=50)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    refresh_at: datetime | None = Field(default=None)

    model_config = ConfigDict(from_attributes=True)
