"""SQLAlchemy declarative base + shared mixins."""
from datetime import datetime
from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class TimestampMixin:
    """Adds created_at / updated_at to a model."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class IdMixin:
    """Adds an integer primary key."""
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
