"""Force-reset all user passwords."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

db = SessionLocal()
try:
    # Ensure admin exists
    admin = db.scalar(select(User).where(User.email == "admin@aviu.ac.ug"))
    if admin:
        admin.hashed_password = hash_password("admin123")
        admin.role = UserRole.ADMIN
        admin.is_active = True
        print("Reset admin password")
    else:
        db.add(User(
            email="admin@aviu.ac.ug",
            full_name="System Administrator",
            hashed_password=hash_password("admin123"),
            role=UserRole.ADMIN,
            is_active=True,
        ))
        print("Created admin")

    # Ensure student exists
    stu = db.scalar(select(User).where(User.email == "student1@aviu.ac.ug"))
    if stu:
        stu.hashed_password = hash_password("student123")
        stu.role = UserRole.STUDENT
        stu.is_active = True
        if not stu.cohort_id:
            stu.cohort_id = "BSE-BC-Y1-Day-Aug2026"
        print("Reset student password")
    else:
        db.add(User(
            email="student1@aviu.ac.ug",
            full_name="Test Student BSE-BC",
            hashed_password=hash_password("student123"),
            role=UserRole.STUDENT,
            cohort_id="BSE-BC-Y1-Day-Aug2026",
            is_active=True,
        ))
        print("Created student")

    # Ensure lecturer exists
    lec = db.scalar(select(User).where(User.email == "lecturer1@aviu.ac.ug"))
    if lec:
        lec.hashed_password = hash_password("lecturer123")
        lec.role = UserRole.LECTURER
        lec.is_active = True
        if not lec.lecturer_id:
            lec.lecturer_id = "LECT-002"
        print("Reset lecturer password")
    else:
        db.add(User(
            email="lecturer1@aviu.ac.ug",
            full_name="Mr. Peter Okello",
            hashed_password=hash_password("lecturer123"),
            role=UserRole.LECTURER,
            lecturer_id="LECT-002",
            is_active=True,
        ))
        print("Created lecturer")

    db.commit()

    print()
    print("=" * 60)
    print("CURRENT USERS")
    print("=" * 60)
    for u in db.query(User).order_by(User.id).all():
        r = u.role.value if hasattr(u.role, "value") else str(u.role)
        print(f"  {u.id}  {u.email:35s}  role={r:10s}  active={u.is_active}")
    print("=" * 60)
finally:
    db.close()