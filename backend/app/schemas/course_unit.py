"""CourseUnit schemas."""
from pydantic import BaseModel
from typing import Optional, List
from app.schemas.common import ORMModel


class CourseUnitBase(BaseModel):
    code: str
    name: str
    credit_units: int = 3
    contact_hours_per_week: int = 3
    normal_year: int = 1
    is_cross_cutting: bool = False
    preferred_room_type: str = "Lecture"
    owning_school: Optional[str] = None
    active: bool = True
    notes: Optional[str] = None


class CourseUnitCreate(CourseUnitBase):
    shared_across_programmes: List[str] = []


class CourseUnitUpdate(BaseModel):
    name: Optional[str] = None
    credit_units: Optional[int] = None
    contact_hours_per_week: Optional[int] = None
    normal_year: Optional[int] = None
    is_cross_cutting: Optional[bool] = None
    preferred_room_type: Optional[str] = None
    owning_school: Optional[str] = None
    active: Optional[bool] = None
    notes: Optional[str] = None


class CourseUnitOut(CourseUnitBase, ORMModel):
    pass
