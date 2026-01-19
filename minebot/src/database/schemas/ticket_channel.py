from pydantic import BaseModel, ConfigDict, PositiveInt


class TicketChannelSchema(BaseModel):
    id: PositiveInt
    owner_id: PositiveInt
    category: str

    model_config = ConfigDict(from_attributes=True)
