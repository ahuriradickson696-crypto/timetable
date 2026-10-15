"""Timetable run + assignment schemas."""
from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from app.schemas.common import ORMModel


class GenerateRequest(BaseModel):
    intake: str = "Aug"
    academic_year: str = "2026/2027"
    semester: int = 1
    run_type: str = "teaching"
    time_limit_seconds: Optional[int] = None
    random_seed: Optional[int] = None


class TimetableAssignmentOut(ORMModel):
    id: int
    activity_id: str
    period_id: int
    room_code: str
    split_group: int
    is_manual: bool = False
    is_locked: bool = False


class TimetableRunOut(ORMModel):
    id: int
    intake: str
    academic_year: str
    semester: int
    run_type: str
    status: str
    solver_params: Optional[str] = None
    metrics: Optional[str] = None
    message: Optional[str] = None
    is_published: bool
    is_locked: bool
    published_at: Optional[datetime] = None
    published_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime


class TimetableRunDetail(TimetableRunOut):
    assignments: List[TimetableAssignmentOut] = []


class TimetableCell(BaseModel):
    day: str
    period_id: str
    start_time: str
    end_time: str
    activity_id: Optional[str] = None
    module_code: Optional[str] = None
    module_name: Optional[str] = None
    cohort_id: Optional[str] = None
    lecturer_id: Optional[str] = None
    lecturer_name: Optional[str] = None
    room_code: Optional[str] = None
    is_break: bool = False
    assignment_id: Optional[int] = None
    is_manual: bool = False
    is_locked: bool = False


class MoveAssignmentRequest(BaseModel):
    """Payload for moving a class to a new period+room."""
    period_id: int
    room_code: str


class MoveAssignmentResponse(BaseModel):
    """Result of a manual move -- reports conflicts if any."""
    status: str  # "ok" or "conflict"
    message: str
    conflicts: List[dict] = []
    assignment: Optional[TimetableAssignmentOut] = None


class ImportResult(BaseModel):
    status: str
    inserted: dict
    updated: dict
    skipped: dict
    errors: List[str] = []
    warnings: List[str] = []