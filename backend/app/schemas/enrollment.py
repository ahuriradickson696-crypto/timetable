"""Enrollment schemas."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.common import ORMModel


class EnrollmentCreate(BaseModel):
    module_code: str
    academic_year: str = "2026/2027"
    semester: int = 1
    notes: Optional[str] = None


class AdminEnrollmentCreate(BaseModel):
    student_id: int
    module_code: str
    academic_year: str = "2026/2027"
    semester: int = 1
    notes: Optional[str] = None


class EnrollmentOut(ORMModel):
    id: int
    student_id: int
    module_code: str
    academic_year: str
    semester: int
    status: str
    grade: Optional[str] = None
    enrolled_at: datetime
    dropped_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    is_locked: bool
    notes: Optional[str] = None
    # Enriched fields
    module_name: Optional[str] = None
    credit_units: Optional[int] = None
    preferred_room_type: Optional[str] = None


class BulkAutoEnrollRequest(BaseModel):
    """Auto-enroll a student in all their cohort's curriculum units."""
    student_id: int
    academic_year: str = "2026/2027"
    semester: int = 1
    replace_existing: bool = False


class EnrollmentStats(BaseModel):
    total_enrolled: int
    total_credits: int
    modules: int