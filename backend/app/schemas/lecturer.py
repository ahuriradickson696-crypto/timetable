"""Lecturer schemas."""
from pydantic import BaseModel
from typing import Optional, List
from app.schemas.common import ORMModel


class LecturerBase(BaseModel):
    id: str
    full_name: str
    max_hours_per_week: int = 16
    preferred_mode: str = "Both"
    unavailable_days: Optional[str] = None
    email: Optional[str] = None
    active: bool = True
    notes: Optional[str] = None


class LecturerCreate(LecturerBase):
    can_teach_modules: List[str] = []


class LecturerUpdate(BaseModel):
    full_name: Optional[str] = None
    max_hours_per_week: Optional[int] = None
    preferred_mode: Optional[str] = None
    unavailable_days: Optional[str] = None
    email: Optional[str] = None
    active: Optional[bool] = None
    notes: Optional[str] = None


class LecturerOut(LecturerBase, ORMModel):
    pass
