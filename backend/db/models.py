import json
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator


class JsonList(TypeDecorator):
    """Store a Python list as a JSON string in a TEXT column."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return "[]"
        return json.dumps(value, ensure_ascii=False)

    def process_result_value(self, value, dialect):
        if not value:
            return []
        try:
            return json.loads(value)
        except Exception:
            return []


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    memory: Mapped["UserMemory"] = relationship(
        "UserMemory", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class UserMemory(Base):
    __tablename__ = "user_memory"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    preferred_origins: Mapped[list] = mapped_column(JsonList, nullable=False, default=list)
    preferred_destinations: Mapped[list] = mapped_column(JsonList, nullable=False, default=list)
    budget_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    budget_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    preferred_hotel_tier: Mapped[str | None] = mapped_column(String(50), nullable=True)
    activity_preferences: Mapped[list] = mapped_column(JsonList, nullable=False, default=list)
    avoidances: Mapped[list] = mapped_column(JsonList, nullable=False, default=list)
    travel_style: Mapped[str | None] = mapped_column(String(100), nullable=True)
    past_trips: Mapped[list] = mapped_column(JsonList, nullable=False, default=list)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship("User", back_populates="memory")
