from sqlalchemy import BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Suggestion(Base):
    __tablename__: str = "suggestions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    staff_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    suggestion: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
