"""Reset student1 enrollments to correct BC-only modules."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import User
from app.models.enrollment import Enrollment
from app.models.cohort import Cohort
from app.models.course_unit import CourseUnit
from app.services.auto_activity import _units_for_cohort

db = SessionLocal()
try:
    stu = db.scalar(select(User).where(User.email == "student1@aviu.ac.ug"))
    if not stu:
        print("Student not found")
        exit(1)

    # Delete ALL existing enrollments
    deleted = db.query(Enrollment).filter(Enrollment.student_id == stu.id).delete()
    db.commit()
    print("Deleted " + str(deleted) + " old enrollments")

    # Get cohort
    cohort = db.get(Cohort, stu.cohort_id)
    if not cohort:
        print("Cohort not found")
        exit(1)

    # Find cohort's BC-specific units
    units = _units_for_cohort(db, cohort, 1)
    # Filter out MT and PY for BC
    if "BC" in stu.cohort_id.upper():
        units = [u for u in units if " MT " not in u.code.upper() and " PY " not in u.code.upper()]

    print("Enrolling " + str(len(units)) + " BC modules:")
    for u in units:
        db.add(Enrollment(
            student_id=stu.id,
            module_code=u.code,
            academic_year="2026/2027",
            semester=1,
            status="enrolled",
        ))
        print("  " + u.code + "  " + u.name)
    db.commit()
    print()
    print("Total enrolled: " + str(db.query(Enrollment).filter(Enrollment.student_id == stu.id, Enrollment.status == "enrolled").count()))
finally:
    db.close()