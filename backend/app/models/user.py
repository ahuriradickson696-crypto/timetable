"""User account model."""
from sqlalchemy import String, Boolean, Enum as SAEnum, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
import enum
from app.db.base import Base, IdMixin, TimestampMixin


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OFFICER = "officer"
    VIEWER = "viewer"
    STUDENT = "student"
    LECTURER = "lecturer"


class User(Base, IdMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, native_enum=False), default=UserRole.VIEWER, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cohort_id: Mapped[str | None] = mapped_column(
        String(100), ForeignKey("cohorts.id"), nullable=True
    )
    lecturer_id: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("lecturers.id"), nullable=True
    )
    last_seen_run_id: Mapped[int | None] = mapped_column(Integer, nullable=True)