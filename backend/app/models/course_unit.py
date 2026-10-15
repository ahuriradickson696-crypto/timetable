"""Course Unit (module) + CourseUnitProgramme junction."""
from sqlalchemy import String, Integer, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from app.db.base import Base, TimestampMixin


class CourseUnit(Base, TimestampMixin):
    __tablename__ = "course_units"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)  # e.g. BSE ED 71101
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    credit_units: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    contact_hours_per_week: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    normal_year: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_cross_cutting: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preferred_room_type: Mapped[str] = mapped_column(String(50), default="Lecture", nullable=False)
    owning_school: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    programme_links: Mapped[List["CourseUnitProgramme"]] = relationship(back_populates="course_unit")
    lecturer_links: Mapped[List["LecturerModule"]] = relationship(back_populates="course_unit")
    activities: Mapped[List["Activity"]] = relationship(back_populates="course_unit")


class CourseUnitProgramme(Base, TimestampMixin):
    """Many-to-many: which programmes share a course unit."""
    __tablename__ = "course_unit_programmes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_unit_code: Mapped[str] = mapped_column(ForeignKey("course_units.code"), nullable=False, index=True)
    programme_code: Mapped[str] = mapped_column(ForeignKey("programmes.code"), nullable=False, index=True)

    course_unit: Mapped["CourseUnit"] = relationship(back_populates="programme_links")
    programme: Mapped["Programme"] = relationship(back_populates="course_unit_links")
