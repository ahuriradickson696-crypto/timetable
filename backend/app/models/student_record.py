"""StudentRecord -- real student data beyond just a login account."""
from sqlalchemy import String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from app.db.base import Base, IdMixin, TimestampMixin


class StudentRecord(Base, IdMixin, TimestampMixin):
    """One student, with their programme, year, semester, combination."""
    __tablename__ = "student_records"

    # Link to login account
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, unique=True, index=True
    )

    # Registration number: AVIU/2026/0001
    student_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )

    # Academic details
    programme_code: Mapped[str] = mapped_column(
        ForeignKey("programmes.code"), nullable=False, index=True
    )
    year_level: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)
    semester: Mapped[int] = mapped_column(Integer, nullable=False, default=1, index=True)
    intake: Mapped[str] = mapped_column(String(20), nullable=False, default="Aug", index=True)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False, default="2026/2027", index=True)

    # Optional combination (BC / MP for BSE)
    combination: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Mode
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="Day")

    # Status
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Active", index=True
    )

    # Optional
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    guardian_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    guardian_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)