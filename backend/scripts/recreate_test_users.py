"""Recreate test users for student + lecturer."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.models.cohort import Cohort
from app.models.lecturer import Lecturer
from app.core.security import hash_password

db = SessionLocal()
try:
    # ---- Student ----
    student_email = "student1@aviu.ac.ug"
    existing = db.scalar(select(User).where(User.email == student_email))
    if existing:
        existing.hashed_password = hash_password("student123")
        existing.cohort_id = "BSE-BC-Y1-Day-Aug2026"
        existing.role = UserRole.STUDENT
        existing.is_active = True
        db.commit()
        print("Updated student user: " + student_email)
    else:
        cohort = db.get(Cohort, "BSE-BC-Y1-Day-Aug2026")
        if not cohort:
            print("WARNING: cohort BSE-BC-Y1-Day-Aug2026 not found!")
        else:
            db.add(User(
                email=student_email,
                full_name="Test Student BSE-BC",
                hashed_password=hash_password("student123"),
                role=UserRole.STUDENT,
                cohort_id="BSE-BC-Y1-Day-Aug2026",
                is_active=True,
            ))
            db.commit()
            print("Created student user: " + student_email)

    # ---- Lecturer ----
    lect_email = "lecturer1@aviu.ac.ug"
    existing = db.scalar(select(User).where(User.email == lect_email))
    if existing:
        existing.hashed_password = hash_password("lecturer123")
        existing.lecturer_id = "LECT-002"
        existing.role = UserRole.LECTURER
        existing.is_active = True
        db.commit()
        print("Updated lecturer user: " + lect_email)
    else:
        lect = db.get(Lecturer, "LECT-002")
        if not lect:
            print("WARNING: lecturer LECT-002 not found!")
        else:
            db.add(User(
                email=lect_email,
                full_name="Mr. Peter Okello",
                hashed_password=hash_password("lecturer123"),
                role=UserRole.LECTURER,
                lecturer_id="LECT-002",
                is_active=True,
            ))
            db.commit()
            print("Created lecturer user: " + lect_email)

    # ---- Print final state ----
    print("")
    print("=" * 60)
    print("CURRENT USERS")
    print("=" * 60)
    for u in db.query(User).all():
        r = u.role.value if hasattr(u.role, "value") else str(u.role)
        print("  " + str(u.id) + "  " + u.email + "  role=" + r + "  cohort=" + (u.cohort_id or "-") + "  lecturer=" + (u.lecturer_id or "-"))
    print("=" * 60)
finally:
    db.close()