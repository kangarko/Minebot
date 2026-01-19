from ..base import BaseSchema


class AuthenticateSchema(BaseSchema, action="authenticate"):
    """Schema for the authenticate action."""

    password: str
    server_list: list[str]
