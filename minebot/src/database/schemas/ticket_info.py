from pydantic import BaseModel, ConfigDict, PositiveInt


class TicketInfoSchema(BaseModel):
    id: PositiveInt
    channel_id: PositiveInt
    message_id: PositiveInt

    model_config = ConfigDict(from_attributes=True)
