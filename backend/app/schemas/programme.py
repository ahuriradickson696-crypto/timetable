"""Programme schemas."""
from pydantic import BaseModel
from typing import Optional
from datetime import date
from app.schemas.common import ORMModel


class ProgrammeBase(BaseModel):
    code: str
    name: str
    level: str
    school_faculty: str
    tier_discipline: Optional[str] = None
    duration_years: int = 3
    last_accreditation: Optional[date] = None
    review_year: Optional[int] = None
    active: bool = True
    notes: Optional[str] = None


class ProgrammeCreate(ProgrammeBase):
    pass


class ProgrammeUpdate(BaseModel):
    name: Optional[str] = None
    level: Optional[str] = None
    school_faculty: Optional[str] = None
    tier_discipline: Optional[str] = None
    duration_years: Optional[int] = None
    last_accreditation: Optional[date] = None
    review_year: Optional[int] = None
    active: Optional[bool] = None
    notes: Optional[str] = None


class ProgrammeOut(ProgrammeBase, ORMModel):
    pass
