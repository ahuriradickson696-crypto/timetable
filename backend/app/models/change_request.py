"""Change request model: lecturers request schedule changes."""
from sqlalchemy import String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime
from app.db.base import Base, IdMixin


class ChangeRequest(Base, IdMixin):
    __tablename__ = "change_requests"

    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("timetable_runs.id"), nullable=True)
    assignment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("timetable_assignments.id"), nullable=True)
    activity_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    request_type: Mapped[str] = mapped_column(String(30), nullable=False)
    current_period_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    desired_period_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    current_room: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    desired_room: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
    reviewer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)