"""Admin-only read API -- EVERY table in the system."""
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.session import get_db
from app.api.deps import get_current_user
from app.api.deps import get_current_user_optional
from app.models.user import User, UserRole
from app.models.programme import Programme
from app.models.cohort import Cohort
from app.models.course_unit import CourseUnit
from app.models.lecturer import Lecturer, LecturerModule
from app.models.room import Room
from app.models.time_period import TimePeriod
from app.models.activity import Activity
from app.models.enrollment import Enrollment
from app.models.timetable import TimetableRun, TimetableAssignment

router = APIRouter(prefix="/api/admin/v1", tags=["admin-api"])


def verify_admin(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    api_key: Optional[str] = None,
    current: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Dual auth:
      1. If X-API-Key header (or ?api_key=) is valid -> allow.
      2. Else if JWT belongs to an admin/officer -> allow.
      3. Else 401/403.
    """
    from app.models.api_key import APIKey
    from datetime import datetime as _dt

    provided = x_api_key or api_key
    if provided:
        row = db.query(APIKey).filter(APIKey.key == provided, APIKey.active == True).first()  # noqa: E712
        if not row:
            raise HTTPException(status_code=401, detail="Invalid or inactive API key")
        row.last_used_at = _dt.utcnow()
        row.call_count = (row.call_count or 0) + 1
        db.commit()
        return row

    if current and current.role.value in ("admin", "officer"):
        return current

    raise HTTPException(status_code=403, detail="Admin access required")

def _user_dict(u):
    return {
        "id": u.id,
        "email": u.email,
        "full_name": u.full_name,
        "role": u.role.value,
        "is_active": u.is_active,
        "cohort_id": u.cohort_id,
        "lecturer_id": u.lecturer_id,
        "created_at": u.created_at.isoformat() if getattr(u, "created_at", None) else None,
    }


@router.get("/")
def root():
    return {
        "name": "AVIU Admin Data API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": [
            "/api/admin/v1/users",
            "/api/admin/v1/users/by-role/{role}",
            "/api/admin/v1/students",
            "/api/admin/v1/employees",
            "/api/admin/v1/admins",
            "/api/admin/v1/programmes",
            "/api/admin/v1/cohorts",
            "/api/admin/v1/course-units",
            "/api/admin/v1/lecturers",
            "/api/admin/v1/lecturer-modules",
            "/api/admin/v1/rooms",
            "/api/admin/v1/time-periods",
            "/api/admin/v1/activities",
            "/api/admin/v1/enrollments",
            "/api/admin/v1/timetable-runs",
            "/api/admin/v1/timetable-assignments",
            "/api/admin/v1/timetable/by-cohort/{cohort_id}",
            "/api/admin/v1/timetable/by-lecturer/{lecturer_id}",
            "/api/admin/v1/timetable/by-room/{room_code}",
            "/api/admin/v1/dump",
        ],
    }


@router.get("/users")
def users(db: Session = Depends(get_db), _=Depends(verify_admin)):
    return [_user_dict(u) for u in db.query(User).order_by(User.id).all()]


@router.get("/users/by-role/{role}")
def users_by_role(role: str, db: Session = Depends(get_db), _=Depends(verify_admin)):
    valid = [r.value for r in UserRole]
    if role.lower() not in valid:
        raise HTTPException(400, "Unknown role: " + role)
    rows = db.query(User).filter(User.role == role.lower()).order_by(User.id).all()
    return [_user_dict(u) for u in rows]


@router.get("/students")
def students(db: Session = Depends(get_db), _=Depends(verify_admin)):
    rows = db.query(User).filter(User.role == UserRole.STUDENT).order_by(User.id).all()
    out = []
    for u in rows:
        c = db.query(Cohort).filter(Cohort.id == u.cohort_id).first() if u.cohort_id else None
        out.append({**_user_dict(u),
                    "cohort_name": c.id if c else None,
                    "programme_code": c.programme_code if c else None,
                    "year_level": c.year_level if c else None})
    return out


@router.get("/employees")
def employees(db: Session = Depends(get_db), _=Depends(verify_admin)):
    rows = db.query(User).filter(User.role != UserRole.STUDENT).order_by(User.id).all()
    return [_user_dict(u) for u in rows]


@router.get("/admins")
def admins(db: Session = Depends(get_db), _=Depends(verify_admin)):
    rows = db.query(User).filter(User.role.in_([UserRole.ADMIN, UserRole.OFFICER])).order_by(User.id).all()
    return [_user_dict(u) for u in rows]


@router.get("/programmes")
def programmes(db: Session = Depends(get_db), _=Depends(verify_admin)):
    return [{
        "code": p.code, "name": p.name, "level": p.level,
        "school_faculty": p.school_faculty,
        "duration_years": p.duration_years,
        "active": p.active, "notes": p.notes,
    } for p in db.query(Programme).order_by(Programme.code).all()]


@router.get("/cohorts")
def cohorts(db: Session = Depends(get_db), _=Depends(verify_admin)):
    return [{
        "id": c.id, "programme_code": c.programme_code,
        "year_level": c.year_level, "mode": c.mode,
        "intake": c.intake, "academic_year": c.academic_year,
        "semester": c.semester, "estimated_students": c.estimated_students,
        "status": c.status,
    } for c in db.query(Cohort).order_by(Cohort.id).all()]


@router.get("/course-units")
def course_units(db: Session = Depends(get_db), _=Depends(verify_admin)):
    return [{
        "code": cu.code, "name": cu.name,
        "credit_units": cu.credit_units,
        "contact_hours_per_week": cu.contact_hours_per_week,
        "normal_year": cu.normal_year,
        "is_cross_cutting": cu.is_cross_cutting,
        "preferred_room_type": cu.preferred_room_type,
        "active": cu.active, "notes": cu.notes,
    } for cu in db.query(CourseUnit).order_by(CourseUnit.code).all()]


@router.get("/lecturers")
def lecturers(db: Session = Depends(get_db), _=Depends(verify_admin)):
    return [{
        "id": l.id, "full_name": l.full_name, "email": l.email,
        "faculty": getattr(l, "faculty", None),
        "max_hours_per_week": l.max_hours_per_week,
        "preferred_mode": l.preferred_mode,
        "active": l.active, "notes": l.notes,
    } for l in db.query(Lecturer).order_by(Lecturer.id).all()]


@router.get("/lecturer-modules")
def lecturer_modules(db: Session = Depends(get_db), _=Depends(verify_admin)):
    return [{
        "id": lm.id,
        "lecturer_id": lm.lecturer_id,
        "course_unit_code": lm.course_unit_code,
    } for lm in db.query(LecturerModule).order_by(LecturerModule.id).all()]


@router.get("/rooms")
def rooms(db: Session = Depends(get_db), _=Depends(verify_admin)):
    return [{
        "code": r.code, "name": r.name, "capacity": r.capacity,
        "room_type": r.room_type, "available_modes": r.available_modes,
        "active": r.active,
    } for r in db.query(Room).order_by(Room.code).all()]


@router.get("/time-periods")
def time_periods(db: Session = Depends(get_db), _=Depends(verify_admin)):
    return [{
        "period_id": tp.period_id, "day": tp.day,
        "start_time": tp.start_time, "end_time": tp.end_time,
        "mode": tp.mode, "is_break": tp.is_break,
    } for tp in db.query(TimePeriod).order_by(TimePeriod.order_index).all()]


@router.get("/activities")
def activities(db: Session = Depends(get_db), _=Depends(verify_admin)):
    return [{
        "id": a.id, "cohort_id": a.cohort_id,
        "module_code": a.module_code, "lecturer_id": a.lecturer_id,
        "duration_periods": a.duration_periods,
        "preferred_room_type": a.preferred_room_type,
        "students": a.students, "semester": a.semester,
        "intake": a.intake, "academic_year": a.academic_year,
        "activity_type": a.activity_type,
    } for a in db.query(Activity).order_by(Activity.id).all()]


@router.get("/enrollments")
def enrollments(db: Session = Depends(get_db), _=Depends(verify_admin)):
    return [{
        "id": e.id, "student_id": e.student_id,
        "module_code": e.module_code,
        "academic_year": e.academic_year, "semester": e.semester,
        "status": e.status,
        "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
    } for e in db.query(Enrollment).order_by(Enrollment.id).all()]


@router.get("/timetable-runs")
def runs(db: Session = Depends(get_db), _=Depends(verify_admin)):
    return [{
        "id": r.id, "intake": r.intake,
        "academic_year": r.academic_year, "semester": r.semester,
        "run_type": r.run_type, "status": r.status,
        "is_published": r.is_published, "message": r.message,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    } for r in db.query(TimetableRun).order_by(TimetableRun.id.desc()).all()]


@router.get("/timetable-assignments")
def assignments(db: Session = Depends(get_db), _=Depends(verify_admin)):
    return [{
        "id": a.id, "run_id": a.run_id,
        "activity_id": a.activity_id, "room_code": a.room_code,
        "period_id": a.period_id,
        "is_manual": getattr(a, "is_manual", False),
        "is_locked": getattr(a, "is_locked", False),
    } for a in db.query(TimetableAssignment).order_by(TimetableAssignment.id).all()]


def _cell(assn, act, tp, cu, lect, room):
    return {
        "day": tp.day, "period_id": tp.period_id,
        "start_time": tp.start_time, "end_time": tp.end_time,
        "module_code": act.module_code,
        "module_name": cu.name if cu else None,
        "cohort_id": act.cohort_id,
        "lecturer_id": act.lecturer_id,
        "lecturer_name": lect.full_name if lect else None,
        "room_code": assn.room_code,
        "room_name": room.name if room else None,
        "activity_type": act.activity_type,
    }


def _published(db):
    run = db.query(TimetableRun).filter(TimetableRun.is_published == True).order_by(TimetableRun.id.desc()).first()  # noqa: E712
    if not run:
        return None, []
    return run, db.query(TimetableAssignment).filter(TimetableAssignment.run_id == run.id).all()


@router.get("/timetable/by-cohort/{cohort_id}")
def tt_cohort(cohort_id: str, db: Session = Depends(get_db), _=Depends(verify_admin)):
    run, rows = _published(db)
    if not run:
        return {"cohort_id": cohort_id, "run_id": None, "classes": []}
    out = []
    for a in rows:
        act = db.query(Activity).filter(Activity.id == a.activity_id).first()
        if not act or act.cohort_id != cohort_id:
            continue
        tp = db.query(TimePeriod).filter(TimePeriod.period_id == a.period_id).first()
        cu = db.query(CourseUnit).filter(CourseUnit.code == act.module_code).first()
        lect = db.query(Lecturer).filter(Lecturer.id == act.lecturer_id).first() if act.lecturer_id else None
        room = db.query(Room).filter(Room.code == a.room_code).first() if a.room_code else None
        out.append(_cell(a, act, tp, cu, lect, room))
    return {"cohort_id": cohort_id, "run_id": run.id, "classes": out}


@router.get("/timetable/by-lecturer/{lecturer_id}")
def tt_lecturer(lecturer_id: str, db: Session = Depends(get_db), _=Depends(verify_admin)):
    run, rows = _published(db)
    if not run:
        return {"lecturer_id": lecturer_id, "run_id": None, "classes": []}
    out = []
    for a in rows:
        act = db.query(Activity).filter(Activity.id == a.activity_id).first()
        if not act or act.lecturer_id != lecturer_id:
            continue
        tp = db.query(TimePeriod).filter(TimePeriod.period_id == a.period_id).first()
        cu = db.query(CourseUnit).filter(CourseUnit.code == act.module_code).first()
        lect = db.query(Lecturer).filter(Lecturer.id == act.lecturer_id).first()
        room = db.query(Room).filter(Room.code == a.room_code).first() if a.room_code else None
        out.append(_cell(a, act, tp, cu, lect, room))
    return {"lecturer_id": lecturer_id, "run_id": run.id, "classes": out}


@router.get("/timetable/by-room/{room_code}")
def tt_room(room_code: str, db: Session = Depends(get_db), _=Depends(verify_admin)):
    run, rows = _published(db)
    if not run:
        return {"room_code": room_code, "run_id": None, "classes": []}
    out = []
    for a in rows:
        if a.room_code != room_code:
            continue
        act = db.query(Activity).filter(Activity.id == a.activity_id).first()
        tp = db.query(TimePeriod).filter(TimePeriod.period_id == a.period_id).first()
        cu = db.query(CourseUnit).filter(CourseUnit.code == act.module_code).first() if act else None
        lect = db.query(Lecturer).filter(Lecturer.id == act.lecturer_id).first() if act and act.lecturer_id else None
        room = db.query(Room).filter(Room.code == a.room_code).first()
        out.append(_cell(a, act, tp, cu, lect, room))
    return {"room_code": room_code, "run_id": run.id, "classes": out}


@router.get("/dump")
def dump(db: Session = Depends(get_db), key=Depends(verify_admin)):
    """Complete system export. Passwords are NEVER included."""
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "counts": {
            "users": db.query(User).count(),
            "students": db.query(User).filter(User.role == UserRole.STUDENT).count(),
            "lecturers": db.query(Lecturer).count(),
            "admins": db.query(User).filter(User.role.in_([UserRole.ADMIN, UserRole.OFFICER])).count(),
            "programmes": db.query(Programme).count(),
            "cohorts": db.query(Cohort).count(),
            "course_units": db.query(CourseUnit).count(),
            "rooms": db.query(Room).count(),
            "time_periods": db.query(TimePeriod).count(),
            "activities": db.query(Activity).count(),
            "enrollments": db.query(Enrollment).count(),
            "timetable_runs": db.query(TimetableRun).count(),
            "timetable_assignments": db.query(TimetableAssignment).count(),
        },
        "users": users(db, key),
        "students": students(db, key),
        "employees": employees(db, key),
        "admins": admins(db, key),
        "programmes": programmes(db, key),
        "cohorts": cohorts(db, key),
        "course_units": course_units(db, key),
        "lecturers": lecturers(db, key),
        "lecturer_modules": lecturer_modules(db, key),
        "rooms": rooms(db, key),
        "time_periods": time_periods(db, key),
        "activities": activities(db, key),
        "enrollments": enrollments(db, key),
        "timetable_runs": runs(db, key),
        "timetable_assignments": assignments(db, key),
    }