"""Activity model - the operational heart (what gets scheduled)."""
from sqlalchemy import String, Integer, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from app.db.base import Base, TimestampMixin


class Activity(Base, TimestampMixin):
    __tablename__ = "activities"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    cohort_id: Mapped[str] = mapped_column(ForeignKey("cohorts.id"), nullable=False, index=True)
    module_code: Mapped[str] = mapped_column(ForeignKey("course_units.code"), nullable=False, index=True)
    lecturer_id: Mapped[str] = mapped_column(ForeignKey("lecturers.id"), nullable=False, index=True)
    duration_periods: Mapped[int] = mapped_column(Integer, nullable=False)
    preferred_room_type: Mapped[str] = mapped_column(String(50), default="Lecture", nullable=False)
    students: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    split_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    joint_cohort_ids: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    semester: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    intake: Mapped[str] = mapped_column(String(20), default="Aug", nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), default="2026/2027", nullable=False)
    # NEW: "teaching" | "test" | "exam"
    activity_type: Mapped[str] = mapped_column(String(20), default="teaching", nullable=False, index=True)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    cohort: Mapped["Cohort"] = relationship(back_populates="activities")
    course_unit: Mapped["CourseUnit"] = relationship(back_populates="activities")
    lecturer: Mapped["Lecturer"] = relationship(back_populates="activities")
    assignments: Mapped[List["TimetableAssignment"]] = relationship(back_populates="activity")