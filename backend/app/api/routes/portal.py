"""Portal endpoints — auto-filtered by the authenticated student / lecturer."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any

from app.db.session import get_db
from app.models.user import User
from app.models.activity import Activity
from app.models.lecturer import Lecturer
from app.models.room import Room
from app.models.course_unit import CourseUnit
from app.models.cohort import Cohort
from app.models.time_period import TimePeriod
from app.models.timetable_run import TimetableRun
from app.models.timetable_assignment import TimetableAssignment
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/portal", tags=["portal"])


def _enrollments_count(db: Session, user: User) -> int:
    """Count active enrollments for a student."""
    if not user.cohort_id:
        return 0
    return db.query(Activity).filter(Activity.cohort_id == user.cohort_id).count()


def _published_run_ids(db: Session) -> List[int]:
    """Only show classes from published runs."""
    rows = db.query(TimetableRun).filter(TimetableRun.is_published == True).all()  # noqa
    return [r.id for r in rows]


def _my_activities(db: Session, user: User) -> List[Activity]:
    """Return activities relevant to this user."""
    q = db.query(Activity)
    if user.role.value == "student":
        if not user.cohort_id:
            return []
        q = q.filter(Activity.cohort_id == user.cohort_id)
    elif user.role.value == "lecturer":
        if not user.lecturer_id:
            return []
        q = q.filter(Activity.lecturer_id == user.lecturer_id)
    else:
        return []
    return q.all()


@router.get("/me")
def portal_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = 0
    if current_user.role.value == "student":
        count = _enrollments_count(db, current_user)
    elif current_user.role.value == "lecturer":
        count = db.query(Activity).filter(Activity.lecturer_id == current_user.lecturer_id).count() if current_user.lecturer_id else 0
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "cohort_id": current_user.cohort_id,
        "lecturer_id": current_user.lecturer_id,
        "enrollment_count": count,
    }


@router.get("/my-timetable")
def my_timetable(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    run_ids = _published_run_ids(db)
    if not run_ids:
        return []
    acts = _my_activities(db, current_user)
    act_ids = [a.id for a in acts]
    if not act_ids:
        return []
    assignments = db.query(TimetableAssignment).filter(
        TimetableAssignment.run_id.in_(run_ids),
        TimetableAssignment.activity_id.in_(act_ids),
    ).all()
    return [_cell(db, a) for a in assignments]


@router.get("/my-next-class")
def my_next_class(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cells = my_timetable(current_user, db)
    if not cells:
        return {}
    now = datetime.now()
    today = now.strftime("%A")
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    today_idx = weekday_order.index(today) if today in weekday_order else 0
    # sort by day then start
    def key(c):
        d = weekday_order.index(c["day"]) if c.get("day") in weekday_order else 99
        return (d, c.get("start_time", "99:99"))
    cells.sort(key=key)
    for c in cells:
        d = weekday_order.index(c["day"]) if c.get("day") in weekday_order else 99
        if d > today_idx:
            return c
        if d == today_idx and c.get("end_time", "00:00") >= now.strftime("%H:%M"):
            return c
    return cells[0] if cells else {}


@router.get("/my-today")
def my_today(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cells = my_timetable(current_user, db)
    today = datetime.now().strftime("%A")
    return [c for c in cells if c.get("day") == today]


@router.get("/my-exams")
def my_exams(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    acts = _my_activities(db, current_user)
    return [{"activity_id": a.id, "module_code": a.module_code, "cohort_id": a.cohort_id, "activity_type": a.activity_type} for a in acts if a.activity_type == "exam"]


@router.get("/activity/{activity_id}/details")
def activity_details(activity_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    a = db.query(Activity).filter(Activity.id == activity_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Activity not found")
    cu = db.query(CourseUnit).filter(CourseUnit.code == a.module_code).first()
    lect = db.query(Lecturer).filter(Lecturer.id == a.lecturer_id).first() if a.lecturer_id else None
    coh = db.query(Cohort).filter(Cohort.id == a.cohort_id).first() if a.cohort_id else None
    return {
        "id": a.id,
        "module_code": a.module_code,
        "module_name": cu.name if cu else "",
        "credit_units": cu.credit_units if cu else None,
        "contact_hours_per_week": cu.contact_hours_per_week if cu else None,
        "preferred_room_type": a.preferred_room_type,
        "activity_type": a.activity_type,
        "duration_periods": a.duration_periods,
        "students": a.students,
        "lecturer_id": a.lecturer_id,
        "lecturer_name": lect.full_name if lect else None,
        "lecturer_email": getattr(lect, "email", None) if lect else None,
        "cohort_id": a.cohort_id,
        "programme_code": coh.programme_code if coh else None,
        "cohort_size": coh.estimated_students if coh else None,
        "notes": cu.notes if cu else None,
        "is_cross_cutting": cu.is_cross_cutting if cu else False,
    }


def _cell(db: Session, a: TimetableAssignment) -> Dict[str, Any]:
    """Build a timetable cell from an assignment."""
    tp = db.query(TimePeriod).filter(TimePeriod.period_id == a.period_id).first()
    act = db.query(Activity).filter(Activity.id == a.activity_id).first()
    cu = db.query(CourseUnit).filter(CourseUnit.code == act.module_code).first() if act else None
    lect = db.query(Lecturer).filter(Lecturer.id == act.lecturer_id).first() if act and act.lecturer_id else None
    room = db.query(Room).filter(Room.code == a.room_code).first() if a.room_code else None
    return {
        "assignment_id": a.id,
        "activity_id": a.activity_id,
        "day": tp.day if tp else "",
        "period_id": a.period_id,
        "start_time": tp.start_time if tp else "",
        "end_time": tp.end_time if tp else "",
        "module_code": act.module_code if act else "",
        "module_name": cu.name if cu else "",
        "cohort_id": act.cohort_id if act else "",
        "lecturer_id": act.lecturer_id if act else "",
        "lecturer_name": lect.full_name if lect else "",
        "room_code": a.room_code,
        "room_name": room.name if room else "",
        "is_break": tp.is_break if tp else False,
        "is_manual": getattr(a, "is_manual", False),
        "is_locked": getattr(a, "is_locked", False),
    }