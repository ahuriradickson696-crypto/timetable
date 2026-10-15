"""Publishing and locking endpoints for timetable runs."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from datetime import datetime

from app.db.session import get_db
from app.api.deps import get_current_user, require_officer, require_admin
from app.models.timetable import TimetableRun
from app.models.user import User
from app.schemas.timetable import TimetableRunOut
from app.services.changelog import log_change


router = APIRouter(prefix="/publishing", tags=["publishing"])


@router.post("/runs/{run_id}/publish", response_model=TimetableRunOut)
def publish_run(
    run_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    """Publish a run as the official timetable for its type.

    Only one run per (intake, academic_year, semester, run_type) can be published.
    Publishing a new run automatically unpublishes the previous one.
    """
    run = db.get(TimetableRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.status != "success":
        raise HTTPException(400, "Can only publish successful runs")

    # Unpublish any other run with the same scope + type
    db.execute(
        update(TimetableRun)
        .where(
            TimetableRun.id != run.id,
            TimetableRun.intake == run.intake,
            TimetableRun.academic_year == run.academic_year,
            TimetableRun.semester == run.semester,
            TimetableRun.run_type == run.run_type,
            TimetableRun.is_published == True,  # noqa: E712
        )
        .values(is_published=False)
    )

    run.is_published = True
    run.is_locked = True
    run.published_at = datetime.utcnow()
    run.published_by = current.id

    log_change(
        db,
        action="publish",
        entity_type="timetable_run",
        entity_id=run.id,
        user_id=current.id,
        run_id=run.id,
        details={
            "run_type": run.run_type,
            "intake": run.intake,
            "academic_year": run.academic_year,
            "semester": run.semester,
        },
    )
    db.commit()
    db.refresh(run)
    return run


@router.post("/runs/{run_id}/unpublish", response_model=TimetableRunOut)
def unpublish_run(
    run_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
):
    """Unpublish a run (admin only). Keeps is_locked to prevent edits until unlocked."""
    run = db.get(TimetableRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    run.is_published = False
    run.published_at = None
    run.published_by = None
    log_change(
        db,
        action="unpublish",
        entity_type="timetable_run",
        entity_id=run.id,
        user_id=current.id,
        run_id=run.id,
    )
    db.commit()
    db.refresh(run)
    return run


@router.post("/runs/{run_id}/unlock", response_model=TimetableRunOut)
def unlock_run(
    run_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
):
    """Remove the lock so the run can be manually edited."""
    run = db.get(TimetableRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    run.is_locked = False
    log_change(
        db,
        action="unlock",
        entity_type="timetable_run",
        entity_id=run.id,
        user_id=current.id,
        run_id=run.id,
    )
    db.commit()
    db.refresh(run)
    return run


@router.get("/runs/published")
def list_published(
    run_type: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all currently published runs."""
    stmt = select(TimetableRun).where(TimetableRun.is_published == True)  # noqa: E712
    if run_type:
        stmt = stmt.where(TimetableRun.run_type == run_type)
    stmt = stmt.order_by(TimetableRun.id.desc())
    return list(db.scalars(stmt))