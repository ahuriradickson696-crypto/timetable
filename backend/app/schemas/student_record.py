"""StudentRecord schemas."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.schemas.common import ORMModel


class StudentRecordBase(BaseModel):
    student_number: Optional[str] = None
    programme_code: str
    year_level: int = Field(default=1, ge=1, le=6)
    semester: int = Field(default=1, ge=1, le=2)
    intake: str = "Aug"
    academic_year: str = "2026/2027"
    combination: Optional[str] = None
    mode: str = "Day"
    status: str = "Active"
    phone: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    notes: Optional[str] = None


class StudentRecordCreate(StudentRecordBase):
    """Create a new student -- also creates the login account."""
    email: EmailStr
    full_name: str
    password: str = Field(min_length=6)


class StudentRecordUpdate(BaseModel):
    programme_code: Optional[str] = None
    year_level: Optional[int] = None
    semester: Optional[int] = None
    intake: Optional[str] = None
    academic_year: Optional[str] = None
    combination: Optional[str] = None
    mode: Optional[str] = None
    status: Optional[str] = None
    phone: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    notes: Optional[str] = None


class StudentRecordOut(ORMModel):
    id: int
    user_id: int
    student_number: str
    programme_code: str
    year_level: int
    semester: int
    intake: str
    academic_year: str
    combination: Optional[str] = None
    mode: str
    status: str
    phone: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None
    notes: Optional[str] = None
    # Enriched
    email: Optional[str] = None
    full_name: Optional[str] = None
    programme_name: Optional[str] = None


class BulkStudentCreate(BaseModel):
    """Bulk-create students from a CSV-style list."""
    students: list[StudentRecordCreate]