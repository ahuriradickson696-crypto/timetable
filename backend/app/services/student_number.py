"""Auto-generate student numbers like AVIU/2026/0001."""
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.models.student_record import StudentRecord


def generate_student_number(db: Session, year: int | None = None) -> str:
    """Generate next sequential number like AVIU/2026/0001."""
    from datetime import datetime
    y = year or datetime.now().year
    prefix = f"AVIU/{y}/"
    # Find the highest existing number for this year
    last = db.scalar(
        select(StudentRecord.student_number)
        .where(StudentRecord.student_number.like(prefix + "%"))
        .order_by(StudentRecord.student_number.desc())
        .limit(1)
    )
    if last:
        try:
            seq = int(last.split("/")[-1]) + 1
        except (ValueError, IndexError):
            seq = 1
    else:
        seq = 1
    return f"{prefix}{seq:04d}"