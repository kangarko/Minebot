from sqlalchemy import BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class TicketChannel(Base):
    __tablename__: str = "ticket_channels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    owner_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
