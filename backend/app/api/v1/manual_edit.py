"""Manual editing of timetable assignments (drag-drop)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.api.deps import get_current_user, require_officer
from app.models.timetable import TimetableRun, TimetableAssignment
from app.models.user import User
from app.schemas.timetable import (
    MoveAssignmentRequest, MoveAssignmentResponse, TimetableAssignmentOut,
)
from app.services.conflict_checker import check_move_conflicts
from app.services.changelog import log_change


router = APIRouter(prefix="/manual-edit", tags=["manual_edit"])


@router.post(
    "/runs/{run_id}/assignments/{assignment_id}/move",
    response_model=MoveAssignmentResponse,
)
def move_assignment(
    run_id: int,
    assignment_id: int,
    body: MoveAssignmentRequest,
    force: bool = False,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    """Move a class to a new period/room. Returns conflicts unless force=True."""
    run = db.get(TimetableRun, run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    if run.is_locked:
        raise HTTPException(400, "Run is locked. Unlock it first.")

    assignment = db.get(TimetableAssignment, assignment_id)
    if not assignment or assignment.run_id != run_id:
        raise HTTPException(404, "Assignment not found in this run")
    if assignment.is_locked:
        raise HTTPException(400, "This entry is locked.")

    # Check for conflicts
    conflicts = check_move_conflicts(
        db, run_id, assignment.activity_id, body.period_id, body.room_code,
        ignore_assignment_id=assignment_id,
    )

    if conflicts and not force:
        return MoveAssignmentResponse(
            status="conflict",
            message=f"{len(conflicts)} conflict(s) found",
            conflicts=conflicts,
        )

    old_period = assignment.period_id
    old_room = assignment.room_code
    assignment.period_id = body.period_id
    assignment.room_code = body.room_code
    assignment.is_manual = True

    log_change(
        db,
        action="move_assignment",
        entity_type="timetable_assignment",
        entity_id=assignment.id,
        user_id=current.id,
        run_id=run_id,
        details={
            "activity_id": assignment.activity_id,
            "from": {"period_id": old_period, "room": old_room},
            "to": {"period_id": body.period_id, "room": body.room_code},
            "forced": force,
        },
    )
    db.commit()
    db.refresh(assignment)

    return MoveAssignmentResponse(
        status="ok",
        message="Moved successfully",
        conflicts=[],
        assignment=TimetableAssignmentOut.model_validate(assignment),
    )


@router.post("/assignments/{assignment_id}/lock")
def lock_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    """Lock an entry so it can't be moved by mistake."""
    a = db.get(TimetableAssignment, assignment_id)
    if not a:
        raise HTTPException(404, "Assignment not found")
    a.is_locked = True
    log_change(
        db, action="lock_assignment", entity_type="timetable_assignment",
        entity_id=a.id, user_id=current.id, run_id=a.run_id,
    )
    db.commit()
    return {"status": "ok", "locked": True}


@router.post("/assignments/{assignment_id}/unlock")
def unlock_assignment(
    assignment_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    """Unlock a previously locked entry."""
    a = db.get(TimetableAssignment, assignment_id)
    if not a:
        raise HTTPException(404, "Assignment not found")
    a.is_locked = False
    log_change(
        db, action="unlock_assignment", entity_type="timetable_assignment",
        entity_id=a.id, user_id=current.id, run_id=a.run_id,
    )
    db.commit()
    return {"status": "ok", "locked": False}


@router.post("/assignments/{assignment_id}/revert")
def revert_to_auto(
    assignment_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    """Clear the is_manual flag (does not move it back)."""
    a = db.get(TimetableAssignment, assignment_id)
    if not a:
        raise HTTPException(404, "Assignment not found")
    a.is_manual = False
    log_change(
        db, action="revert_to_auto", entity_type="timetable_assignment",
        entity_id=a.id, user_id=current.id, run_id=a.run_id,
    )
    db.commit()
    return {"status": "ok"}