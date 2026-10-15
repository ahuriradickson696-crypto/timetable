"""Activity schemas."""
from pydantic import BaseModel
from typing import Optional, List
from app.schemas.common import ORMModel


class ActivityBase(BaseModel):
    id: str
    cohort_id: str
    module_code: str
    lecturer_id: str
    duration_periods: int
    preferred_room_type: str = "Lecture"
    students: int = 0
    split_allowed: bool = True
    joint_cohort_ids: Optional[str] = None
    semester: int = 1
    intake: str = "Aug"
    academic_year: str = "2026/2027"
    activity_type: str = "teaching"
    notes: Optional[str] = None


class ActivityCreate(ActivityBase):
    pass


class ActivityUpdate(BaseModel):
    cohort_id: Optional[str] = None
    module_code: Optional[str] = None
    lecturer_id: Optional[str] = None
    duration_periods: Optional[int] = None
    preferred_room_type: Optional[str] = None
    students: Optional[int] = None
    split_allowed: Optional[bool] = None
    joint_cohort_ids: Optional[str] = None
    semester: Optional[int] = None
    intake: Optional[str] = None
    academic_year: Optional[str] = None
    activity_type: Optional[str] = None
    notes: Optional[str] = None


class ActivityOut(ActivityBase, ORMModel):
    pass