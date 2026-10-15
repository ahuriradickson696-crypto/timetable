"""Change log for tracking timetable edits."""
from sqlalchemy import String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from datetime import datetime
from app.db.base import Base, IdMixin


class ChangeLog(Base, IdMixin):
    __tablename__ = "change_log"

    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    run_id: Mapped[Optional[int]] = mapped_column(ForeignKey("timetable_runs.id"), nullable=True, index=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)