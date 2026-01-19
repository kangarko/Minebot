from ..base import ServerBaseSchema


class CommandExecutedSchema(ServerBaseSchema, action="command-executed"):
    """Schema for the command-executed action."""

    command_type: str
    executor: str
    args: dict[str, str] | None = None
