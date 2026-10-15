"""TimePeriod schemas."""
from pydantic import BaseModel
from typing import Optional
from app.schemas.common import ORMModel


class TimePeriodBase(BaseModel):
    period_id: str
    day: str
    start_time: str
    end_time: str
    mode: str
    is_break: bool = False
    order_index: int = 0


class TimePeriodCreate(TimePeriodBase):
    pass


class TimePeriodUpdate(BaseModel):
    period_id: Optional[str] = None
    day: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    mode: Optional[str] = None
    is_break: Optional[bool] = None
    order_index: Optional[int] = None


class TimePeriodOut(TimePeriodBase, ORMModel):
    id: int
