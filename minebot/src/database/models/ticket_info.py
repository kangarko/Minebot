from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class TicketInfo(Base):
    __tablename__: str = "ticket_info"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
