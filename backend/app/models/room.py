"""Room / Laboratory model."""
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from app.db.base import Base, TimestampMixin


class Room(Base, TimestampMixin):
    __tablename__ = "rooms"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)  # e.g. MH-01, CL-01
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    room_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Lecture / Computer Lab / Science Lab / Clinical Lab / Seminar
    building: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    features: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    available_modes: Mapped[str] = mapped_column(String(20), default="Both", nullable=False)  # Day / Weekend / Both
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    assignments: Mapped[List["TimetableAssignment"]] = relationship(back_populates="room")
