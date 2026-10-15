"""Check whether moving an assignment creates a clash."""
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.timetable import TimetableAssignment, TimetableRun
from app.models.activity import Activity
from app.models.time_period import TimePeriod


def check_move_conflicts(
    db: Session,
    run_id: int,
    activity_id: str,
    new_period_id: int,
    new_room_code: str,
    ignore_assignment_id: int | None = None,
) -> List[Dict]:
    """Return a list of conflicts if the move is invalid.

    Empty list = safe to move.
    """
    conflicts: List[Dict] = []

    activity = db.get(Activity, activity_id)
    if not activity:
        return [{"type": "error", "message": f"Activity {activity_id} not found"}]

    new_period = db.get(TimePeriod, new_period_id)
    if not new_period:
        return [{"type": "error", "message": f"Period {new_period_id} not found"}]

    # Load all assignments in this run
    stmt = select(TimetableAssignment).where(TimetableAssignment.run_id == run_id)
    if ignore_assignment_id is not None:
        stmt = stmt.where(TimetableAssignment.id != ignore_assignment_id)
    other_assignments = list(db.scalars(stmt))

    # 1. Room clash at new period
    for a in other_assignments:
        if a.period_id == new_period_id and a.room_code == new_room_code:
            conflicts.append({
                "type": "room_clash",
                "message": f"Room {new_room_code} already booked at this period",
                "conflicting_activity": a.activity_id,
            })

    # 2. Lecturer clash (same lecturer, same period)
    for a in other_assignments:
        if a.period_id != new_period_id:
            continue
        other_act = db.get(Activity, a.activity_id)
        if other_act and other_act.lecturer_id == activity.lecturer_id:
            conflicts.append({
                "type": "lecturer_clash",
                "message": f"Lecturer {activity.lecturer_id} already teaching at this period",
                "conflicting_activity": a.activity_id,
            })

    # 3. Cohort clash (same cohort, same period)
    for a in other_assignments:
        if a.period_id != new_period_id:
            continue
        other_act = db.get(Activity, a.activity_id)
        if not other_act:
            continue
        if other_act.cohort_id == activity.cohort_id:
            conflicts.append({
                "type": "cohort_clash",
                "message": f"Cohort {activity.cohort_id} already has a class at this period",
                "conflicting_activity": a.activity_id,
            })

    return conflicts