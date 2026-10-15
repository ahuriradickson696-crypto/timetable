"""Link existing student users to StudentRecords."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.student_record import StudentRecord
from app.models.cohort import Cohort
from app.models.programme import Programme
from app.services.student_number import generate_student_number

db = SessionLocal()
try:
    # Find all student users without a StudentRecord
    students = list(db.scalars(select(User).where(User.role == UserRole.STUDENT)))

    print("Found " + str(len(students)) + " student users")
    print()

    for u in students:
        existing = db.scalar(select(StudentRecord).where(StudentRecord.user_id == u.id))
        if existing:
            print("  SKIP: " + u.email + " (already has record " + existing.student_number + ")")
            continue

        # Look up their cohort
        cohort = db.get(Cohort, u.cohort_id) if u.cohort_id else None
        if not cohort:
            print("  WARN: " + u.email + " has no cohort linked, skipping")
            continue

        # Check programme exists
        if not db.get(Programme, cohort.programme_code):
            print("  WARN: programme " + cohort.programme_code + " not found for " + u.email)
            continue

        # Extract combination from cohort ID (BSE-BC-... → "BC")
        combination = None
        if "-BC-" in cohort.id or "-BC" in cohort.id:
            combination = "BC"
        elif "-MP-" in cohort.id or "-MP" in cohort.id:
            combination = "MP"

        student_number = generate_student_number(db, 2026)

        sr = StudentRecord(
            user_id=u.id,
            student_number=student_number,
            programme_code=cohort.programme_code,
            year_level=cohort.year_level,
            semester=cohort.semester,
            intake=cohort.intake,
            academic_year=cohort.academic_year,
            combination=combination,
            mode=cohort.mode,
            status="Active",
            notes="Migrated from user account",
        )
        db.add(sr)
        db.flush()
        print("  LINK: " + u.email + " -> " + student_number + " (" + cohort.programme_code + ", Y" + str(cohort.year_level) + ", Sem " + str(cohort.semester) + (", " + combination if combination else "") + ")")

    db.commit()

    print()
    print("=" * 60)
    print("STUDENT RECORDS")
    print("=" * 60)
    for sr in db.query(StudentRecord).all():
        u = db.get(User, sr.user_id)
        print("  " + sr.student_number + "  " + (u.email if u else "?") + "  " + sr.programme_code + "  Y" + str(sr.year_level) + " S" + str(sr.semester) + "  " + (sr.combination or "-"))
    print("=" * 60)
finally:
    db.close()