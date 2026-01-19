from pydantic import BaseModel, ConfigDict, PositiveInt


class SuggestionSchema(BaseModel):
    id: PositiveInt
    user_id: PositiveInt
    staff_id: PositiveInt | None = None
    suggestion: str
    status: str

    model_config = ConfigDict(from_attributes=True)
