from pydantic import BaseModel, ConfigDict, Field, PositiveInt, field_validator

from core import GlobalState


class UserSchema(BaseModel):
    id: PositiveInt
    locale: str
    minecraft_username: str | None = Field(default=None, max_length=16)
    minecraft_uuid: str | None = Field(default=None, max_length=36)
    reward_inventory: dict[str, list[str]] | None = Field(default=None)

    @field_validator("reward_inventory")
    @classmethod
    def validate_reward_inventory(
        cls, v: dict[str, list[str]] | None
    ) -> dict[str, list[str]] | None:
        if v is None or not v:  # Return early if None or empty dict
            return v

        MINECRAFT_SERVERS = GlobalState.minecraft.get_servers()

        # If MINECRAFT_SERVERS is empty or None, skip validation
        if not MINECRAFT_SERVERS:
            return v

        server_set = set(MINECRAFT_SERVERS)

        # Check for invalid keys
        invalid_keys = [key for key in v if key not in server_set]

        if invalid_keys:
            raise ValueError(
                f"Invalid server keys: {invalid_keys}. Allowed keys are: {MINECRAFT_SERVERS}"
            )

        return v

    model_config = ConfigDict(from_attributes=True)
