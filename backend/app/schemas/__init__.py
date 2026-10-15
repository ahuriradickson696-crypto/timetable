"""Re-export all schemas for convenience."""
from app.schemas.common import ORMModel, Message
from app.schemas.auth import (
    LoginRequest, TokenResponse, UserOut, UserCreate, UserUpdate,
)
from app.schemas.programme import ProgrammeCreate, ProgrammeUpdate, ProgrammeOut
from app.schemas.cohort import CohortCreate, CohortUpdate, CohortOut
from app.schemas.course_unit import CourseUnitCreate, CourseUnitUpdate, CourseUnitOut
from app.schemas.lecturer import LecturerCreate, LecturerUpdate, LecturerOut
from app.schemas.room import RoomCreate, RoomUpdate, RoomOut
from app.schemas.time_period import TimePeriodCreate, TimePeriodUpdate, TimePeriodOut
from app.schemas.activity import ActivityCreate, ActivityUpdate, ActivityOut
from app.schemas.timetable import (
    GenerateRequest, TimetableRunOut, TimetableRunDetail,
    TimetableAssignmentOut, TimetableCell, ImportResult,
)

__all__ = [
    "ORMModel", "Message",
    "LoginRequest", "TokenResponse", "UserOut", "UserCreate", "UserUpdate",
    "ProgrammeCreate", "ProgrammeUpdate", "ProgrammeOut",
    "CohortCreate", "CohortUpdate", "CohortOut",
    "CourseUnitCreate", "CourseUnitUpdate", "CourseUnitOut",
    "LecturerCreate", "LecturerUpdate", "LecturerOut",
    "RoomCreate", "RoomUpdate", "RoomOut",
    "TimePeriodCreate", "TimePeriodUpdate", "TimePeriodOut",
    "ActivityCreate", "ActivityUpdate", "ActivityOut",
    "GenerateRequest", "TimetableRunOut", "TimetableRunDetail",
    "TimetableAssignmentOut", "TimetableCell", "ImportResult",
]
