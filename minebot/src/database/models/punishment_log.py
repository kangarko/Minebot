from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class PunishmentLog(Base):
    __tablename__: str = "punishment_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    punishment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    staff_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    duration: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
