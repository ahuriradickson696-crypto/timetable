"""Clean the DB and prepare for full curriculum import."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.programme import Programme
from app.models.cohort import Cohort
from app.models.course_unit import CourseUnit
from app.models.activity import Activity
from app.models.enrollment import Enrollment
from app.models.student_record import StudentRecord

db = SessionLocal()
try:
    print("=" * 70)
    print("DATABASE CLEANUP REPORT")
    print("=" * 70)

    # 1. Programmes
    progs = list(db.scalars(select(Programme)))
    print(f"\nProgrammes: {len(progs)}")
    for p in progs:
        print(f"  {p.code:8s}  level={p.level:12s}  name={p.name}")

    # 2. Course units
    units = list(db.scalars(select(CourseUnit)))
    print(f"\nCourse units: {len(units)}")

    # 3. Cohorts
    cohorts = list(db.scalars(select(Cohort)))
    print(f"Cohorts: {len(cohorts)}")

    # 4. Activities
    acts = list(db.scalars(select(Activity)))
    print(f"Activities: {len(acts)}")

    # 5. Enrollments
    enrs = list(db.scalars(select(Enrollment)))
    print(f"Enrollments: {len(enrs)}")

    # 6. Students
    srs = list(db.scalars(select(StudentRecord)))
    print(f"Student records: {len(srs)}")

    print()
    print("=" * 70)
finally:
    db.close()