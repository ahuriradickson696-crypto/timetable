"""Cohort schemas."""
from pydantic import BaseModel
from typing import Optional
from app.schemas.common import ORMModel


class CohortBase(BaseModel):
    id: str
    programme_code: str
    year_level: int
    mode: str
    intake: str
    academic_year: str
    semester: int
    estimated_students: int = 0
    status: str = "Active"


class CohortCreate(CohortBase):
    pass


class CohortUpdate(BaseModel):
    year_level: Optional[int] = None
    mode: Optional[str] = None
    intake: Optional[str] = None
    academic_year: Optional[str] = None
    semester: Optional[int] = None
    estimated_students: Optional[int] = None
    status: Optional[str] = None


class CohortOut(CohortBase, ORMModel):
    pass
