from pydantic import field_validator

from ..base import ServerBaseSchema


class DispatchCommandSchema(ServerBaseSchema, action="dispatch-command"):
    """Schema for the dispatch-command action."""

    commands: str | list[str]

    @field_validator("commands")
    @classmethod
    def normalize_commands(cls, v) -> list[str]:
        return v if isinstance(v, list) else [v]
