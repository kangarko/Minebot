from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class TemporaryAction(Base):
    __tablename__: str = "temporary_actions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    punishment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    refresh_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
