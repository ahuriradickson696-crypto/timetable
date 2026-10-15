"""Add Exam and Test time grids, and sample exam activities."""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.time_period import TimePeriod
from app.models.activity import Activity
from app.models.cohort import Cohort
from app.models.course_unit import CourseUnit
from app.models.lecturer import Lecturer
from app.db.base import Base
from app.db.session import engine


# 4 slots/day for exams (2 hours each), Mon-Sat
EXAM_SLOTS = [
    ("08:00", "10:00"),
    ("10:30", "12:30"),
    ("14:00", "16:00"),
    ("16:30", "18:30"),
]

# 4 slots/day for tests (1 hour each), Mon-Sat
TEST_SLOTS = [
    ("08:00", "09:00"),
    ("09:00", "10:00"),
    ("14:00", "15:00"),
    ("15:00", "16:00"),
]


def add_time_grid(db, mode: str, slots: list[tuple[str, str]]):
    """Add time periods for the given mode across Mon-Sat."""
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    added = 0
    for day_idx, day in enumerate(days):
        for slot_idx, (start, end) in enumerate(slots):
            pid = f"{mode[0]}-P{slot_idx + 1}"  # E-P1..E-P4 or T-P1..T-P4
            exists = db.scalar(
                select(TimePeriod).where(
                    TimePeriod.period_id == pid,
                    TimePeriod.day == day,
                    TimePeriod.mode == mode,
                )
            )
            if exists:
                continue
            db.add(
                TimePeriod(
                    period_id=pid,
                    day=day,
                    start_time=start,
                    end_time=end,
                    mode=mode,
                    is_break=False,
                    order_index=day_idx * 100 + slot_idx,
                )
            )
            added += 1
    db.commit()
    return added


def add_sample_exams(db):
    """Create exam activities for cohort X's Semester 1 modules."""
    # Map cohort -> list of modules that should have exams (non-practical)
    exam_map = {
        "BSE-BC-Y1-Day-Aug2026": [
            ("BSE ED 71101", "LECT-002", "EX-BC-001"),
            ("BSE ED 71102", "LECT-002", "EX-BC-002"),
            ("BSE BI 71105", "LECT-005", "EX-BC-003"),
            ("BSE CH 71107", "LECT-006", "EX-BC-004"),
        ],
        "BSE-MP-Y1-Day-Aug2026": [
            ("BSE ED 71101", "LECT-002", "EX-MP-001"),
            ("BSE ED 71102", "LECT-002", "EX-MP-002"),
            ("BSE MT 71109", "LECT-007", "EX-MP-003"),
            ("BSE MT 71110", "LECT-007", "EX-MP-004"),
        ],
        "DCM-Y1-Day-Aug2026": [
            ("DCM BC 51104", "LECT-011", "EX-DCM-001"),
            ("DCM MB 51105", "LECT-012", "EX-DCM-002"),
            ("DCM CM 51106", "LECT-016", "EX-DCM-003"),
        ],
        "DMLT-Y1-Day-Aug2026": [
            ("DMLT LB 51104", "LECT-018", "EX-DMLT-001"),
            ("DMLT MB 51105", "LECT-012", "EX-DMLT-002"),
            ("DMLT CC 51106", "LECT-018", "EX-DMLT-003"),
        ],
    }

    added = 0
    for cohort_id, modules in exam_map.items():
        if not db.get(Cohort, cohort_id):
            continue
        for module_code, lecturer_id, aid in modules:
            if db.get(Activity, aid):
                continue
            if not db.get(CourseUnit, module_code):
                continue
            if not db.get(Lecturer, lecturer_id):
                continue
            db.add(Activity(
                id=aid,
                cohort_id=cohort_id,
                module_code=module_code,
                lecturer_id=lecturer_id,
                duration_periods=1,   # 1 exam slot = 2 hours (handled by period length)
                preferred_room_type="Lecture",
                students=30,
                split_allowed=False,
                joint_cohort_ids=None,
                semester=1,
                intake="Aug",
                academic_year="2026/2027",
                activity_type="exam",
                notes="Sample final exam",
            ))
            added += 1
    db.commit()
    return added


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        n1 = add_time_grid(db, "Exam", EXAM_SLOTS)
        n2 = add_time_grid(db, "Test", TEST_SLOTS)
        n3 = add_sample_exams(db)
        print(f"Added {n1} exam periods")
        print(f"Added {n2} test periods")
        print(f"Added {n3} sample exam activities")
    finally:
        db.close()


if __name__ == "__main__":
    main()