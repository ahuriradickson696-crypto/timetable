"""Reset student1 enrollments, then auto-enroll correctly."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import User
from app.models.enrollment import Enrollment

db = SessionLocal()
try:
    student = db.scalar(select(User).where(User.email == "student1@aviu.ac.ug"))
    if not student:
        print("Student not found")
        exit(1)

    # Delete all existing enrollments
    deleted = db.query(Enrollment).filter(Enrollment.student_id == student.id).delete()
    db.commit()
    print("Deleted " + str(deleted) + " enrollments")
    print("Now run auto-enroll again via API or browser")
finally:
    db.close()