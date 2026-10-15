"""Timetable generation + view endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from typing import List, Optional

from app.db.session import get_db
from app.api.deps import get_current_user, require_officer
from app.models.timetable import TimetableRun, TimetableAssignment
from app.models.activity import Activity
from app.models.time_period import TimePeriod
from app.models.course_unit import CourseUnit
from app.models.lecturer import Lecturer
from app.models.room import Room
from app.models.cohort import Cohort
from app.models.user import User
from app.schemas.timetable import (
    GenerateRequest, TimetableRunOut, TimetableRunDetail, TimetableCell,
)
from app.services.solver.runner import generate_timetable

router = APIRouter(prefix="/generation", tags=["generation"])


@router.post("/generate", response_model=TimetableRunOut)
def generate(
    body: GenerateRequest,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    return generate_timetable(
        db=db,
        intake=body.intake,
        academic_year=body.academic_year,
        semester=body.semester,
        run_type=body.run_type,
        created_by=current.id,
        time_limit=body.time_limit_seconds,
        seed=body.random_seed,
    )


@router.get("/runs", response_model=list[TimetableRunOut])
def list_runs(
    run_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(TimetableRun).order_by(TimetableRun.id.desc())
    if run_type:
        stmt = stmt.where(TimetableRun.run_type == run_type)
    return list(db.scalars(stmt))


@router.get("/runs/{run_id}", response_model=TimetableRunDetail)
def get_run(
    run_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    run = db.get(TimetableRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return run


@router.get("/runs/{run_id}/by-cohort/{cohort_id}", response_model=list[TimetableCell])
def view_by_cohort(run_id: int, cohort_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return _view(db, run_id, cohort_id=cohort_id)


@router.get("/runs/{run_id}/by-lecturer/{lecturer_id}", response_model=list[TimetableCell])
def view_by_lecturer(run_id: int, lecturer_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return _view(db, run_id, lecturer_id=lecturer_id)


@router.get("/runs/{run_id}/by-room/{room_code}", response_model=list[TimetableCell])
def view_by_room(run_id: int, room_code: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return _view(db, run_id, room_code=room_code)


@router.get("/runs/{run_id}/by-programme/{programme_code}", response_model=list[TimetableCell])
def view_by_programme(run_id: int, programme_code: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Return all activities for cohorts in the given programme."""
    return _view(db, run_id, programme_code=programme_code)


@router.get("/runs/{run_id}/by-module/{module_code:path}", response_model=list[TimetableCell])
def view_by_module(run_id: int, module_code: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Return all activities for a given module code."""
    return _view(db, run_id, module_code=module_code)


def _view(
    db: Session,
    run_id: int,
    cohort_id: str | None = None,
    lecturer_id: str | None = None,
    room_code: str | None = None,
    programme_code: str | None = None,
    module_code: str | None = None,
) -> List[TimetableCell]:
    stmt = select(TimetableAssignment, Activity, TimePeriod).join(
        Activity, TimetableAssignment.activity_id == Activity.id
    ).join(
        TimePeriod, TimetableAssignment.period_id == TimePeriod.id
    ).where(TimetableAssignment.run_id == run_id)

    if cohort_id:
        stmt = stmt.where(Activity.cohort_id == cohort_id)
    if lecturer_id:
        stmt = stmt.where(Activity.lecturer_id == lecturer_id)
    if room_code:
        stmt = stmt.where(TimetableAssignment.room_code == room_code)
    if programme_code:
        cohort_ids = [c.id for c in db.scalars(
            select(Cohort).where(Cohort.programme_code == programme_code)
        )]
        if not cohort_ids:
            return []
        stmt = stmt.where(Activity.cohort_id.in_(cohort_ids))
    if module_code:
        stmt = stmt.where(Activity.module_code == module_code)

    rows = db.execute(stmt).all()
    cells: List[TimetableCell] = []
    for assn, act, per in rows:
        cu = db.get(CourseUnit, act.module_code)
        lect = db.get(Lecturer, act.lecturer_id)
        cells.append(TimetableCell(
            day=per.day,
            period_id=per.period_id,
            start_time=per.start_time,
            end_time=per.end_time,
            activity_id=act.id,
            module_code=act.module_code,
            module_name=cu.name if cu else None,
            cohort_id=act.cohort_id,
            lecturer_id=act.lecturer_id,
            lecturer_name=lect.full_name if lect else None,
            room_code=assn.room_code,
            is_break=per.is_break,
            assignment_id=assn.id,
            is_manual=assn.is_manual,
            is_locked=assn.is_locked,
        ))
    return cells


# ============================================================
# Export endpoints
# ============================================================
from fastapi.responses import Response


@router.get("/runs/{run_id}/export/excel")
def export_excel(run_id: int, view: str = "cohort", key: str = "", db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    from app.services.export import build_excel
    cells = _export_view(db, run_id, view, key)
    title = "AVIU Timetable - " + view + ": " + key
    data = build_excel(title, [c.model_dump() for c in cells])
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=aviu-timetable-{view}-{key}.xlsx"},
    )


@router.get("/runs/{run_id}/export/pdf")
def export_pdf(run_id: int, view: str = "cohort", key: str = "", db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    from app.services.export import build_pdf
    cells = _export_view(db, run_id, view, key)
    title = "AVIU Timetable - " + view + ": " + key
    data = build_pdf(title, [c.model_dump() for c in cells])
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=aviu-timetable-{view}-{key}.pdf"},
    )


def _export_view(db: Session, run_id: int, view: str, key: str):
    if view == "cohort":
        return _view(db, run_id, cohort_id=key)
    elif view == "lecturer":
        return _view(db, run_id, lecturer_id=key)
    elif view == "room":
        return _view(db, run_id, room_code=key)
    elif view == "programme":
        return _view(db, run_id, programme_code=key)
    elif view == "module":
        return _view(db, run_id, module_code=key)
    raise HTTPException(400, "Unknown view: " + view)