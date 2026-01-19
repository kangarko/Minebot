from sqlalchemy import JSON, BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class User(Base):
    __tablename__: str = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    locale: Mapped[str] = mapped_column(String(5), nullable=False)
    minecraft_username: Mapped[str | None] = mapped_column(String(16), nullable=True)
    minecraft_uuid: Mapped[str | None] = mapped_column(String(36), nullable=True)
    reward_inventory: Mapped[dict[str, list[str]] | None] = mapped_column(JSON, nullable=True)
