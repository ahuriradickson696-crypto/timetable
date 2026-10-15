"""Student enrollment model -- which modules a student takes."""
from sqlalchemy import String, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
from app.db.base import Base, IdMixin, TimestampMixin


class Enrollment(Base, IdMixin, TimestampMixin):
    """A single enrollment: student X is taking module Y in semester Z."""
    __tablename__ = "enrollments"

    student_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    module_code: Mapped[str] = mapped_column(
        ForeignKey("course_units.code"), nullable=False, index=True
    )
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    semester: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # enrolled | completed | dropped
    status: Mapped[str] = mapped_column(String(20), default="enrolled", nullable=False, index=True)

    # Optional: grade, when completed
    grade: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    enrolled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    dropped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Set by admin to prevent student from dropping
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)