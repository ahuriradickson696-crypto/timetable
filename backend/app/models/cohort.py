"""Cohort model (Programme + Year + Mode + Intake)."""
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from app.db.base import Base, TimestampMixin


class Cohort(Base, TimestampMixin):
    __tablename__ = "cohorts"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # e.g. BSE-BC-Y1-Day-Aug2026
    programme_code: Mapped[str] = mapped_column(ForeignKey("programmes.code"), nullable=False, index=True)
    year_level: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)  # Day / Weekend
    intake: Mapped[str] = mapped_column(String(20), nullable=False)  # Jan / May / Aug
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. 2026/2027
    semester: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 or 2
    estimated_students: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="Active", nullable=False)

    programme: Mapped["Programme"] = relationship(back_populates="cohorts")
    activities: Mapped[List["Activity"]] = relationship(back_populates="cohort")
