"""Programme model (NCHE accredited programmes)."""
from sqlalchemy import String, Integer, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
from typing import Optional, List
from app.db.base import Base, TimestampMixin


class Programme(Base, TimestampMixin):
    __tablename__ = "programmes"

    code: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False)  # Bachelor, Diploma, Masters, PG Diploma, Certificate
    school_faculty: Mapped[str] = mapped_column(String(255), nullable=False)
    tier_discipline: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    duration_years: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    last_accreditation: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    review_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    cohorts: Mapped[List["Cohort"]] = relationship(back_populates="programme")
    course_unit_links: Mapped[List["CourseUnitProgramme"]] = relationship(back_populates="programme")
