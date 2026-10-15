"""TimePeriod model (Day and Weekend grids)."""
from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin


class TimePeriod(Base, TimestampMixin):
    __tablename__ = "time_periods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    period_id: Mapped[str] = mapped_column(String(20), nullable=False)  # D-P1, D-B1, W-P1
    day: Mapped[str] = mapped_column(String(20), nullable=False)  # Monday..Sunday
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)  # HH:MM
    end_time: Mapped[str] = mapped_column(String(10), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)  # Day / Weekend
    is_break: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # position in day
