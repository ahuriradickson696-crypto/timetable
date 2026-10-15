"""Check what student1 is enrolled in."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import User
from app.models.enrollment import Enrollment
from app.models.course_unit import CourseUnit

db = SessionLocal()
try:
    stu = db.scalar(select(User).where(User.email == "student1@aviu.ac.ug"))
    print("Student:", stu.email, "cohort:", stu.cohort_id)
    print()

    enrollments = list(db.scalars(
        select(Enrollment).where(
            Enrollment.student_id == stu.id,
            Enrollment.status == "enrolled",
        )
    ))
    print("Enrolled modules:", len(enrollments))
    for e in enrollments:
        cu = db.get(CourseUnit, e.module_code)
        print(f"  {e.module_code:25s}  {cu.name if cu else '?'}")
finally:
    db.close()