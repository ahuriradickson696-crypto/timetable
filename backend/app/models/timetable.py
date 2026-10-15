"""TimetableRun and TimetableAssignment models."""
from sqlalchemy import String, Integer, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from datetime import datetime
from app.db.base import Base, TimestampMixin


class TimetableRun(Base, TimestampMixin):
    __tablename__ = "timetable_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    intake: Mapped[str] = mapped_column(String(20), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    semester: Mapped[int] = mapped_column(Integer, nullable=False)
    run_type: Mapped[str] = mapped_column(String(20), default="teaching", nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    solver_params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metrics: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    published_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    assignments: Mapped[List["TimetableAssignment"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class TimetableAssignment(Base, TimestampMixin):
    __tablename__ = "timetable_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("timetable_runs.id"), nullable=False, index=True)
    activity_id: Mapped[str] = mapped_column(ForeignKey("activities.id"), nullable=False, index=True)
    period_id: Mapped[int] = mapped_column(ForeignKey("time_periods.id"), nullable=False, index=True)
    room_code: Mapped[str] = mapped_column(ForeignKey("rooms.code"), nullable=False, index=True)
    split_group: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # Manual edit tracking
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    run: Mapped["TimetableRun"] = relationship(back_populates="assignments")
    activity: Mapped["Activity"] = relationship(back_populates="assignments")
    period: Mapped["TimePeriod"] = relationship()
    room: Mapped["Room"] = relationship(back_populates="assignments")