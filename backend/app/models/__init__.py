"""Import all models so Base.metadata sees them."""
from app.models.user import User, UserRole
from app.models.programme import Programme
from app.models.cohort import Cohort
from app.models.course_unit import CourseUnit, CourseUnitProgramme
from app.models.lecturer import Lecturer, LecturerModule
from app.models.room import Room
from app.models.time_period import TimePeriod
from app.models.activity import Activity
from app.models.timetable import TimetableRun, TimetableAssignment
from app.models.change_log import ChangeLog
from app.models.change_request import ChangeRequest
from app.models.enrollment import Enrollment
from app.models.student_record import StudentRecord

__all__ = [
    "User", "UserRole",
    "Programme", "Cohort",
    "CourseUnit", "CourseUnitProgramme",
    "Lecturer", "LecturerModule",
    "Room", "TimePeriod", "Activity",
    "TimetableRun", "TimetableAssignment",
    "ChangeLog", "ChangeRequest",
    "Enrollment", "StudentRecord",
]
from app.models.api_key import APIKey  # noqa: F401
