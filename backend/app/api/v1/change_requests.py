"""Change request endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.db.session import get_db
from app.api.deps import get_current_user, require_officer
from app.models.change_request import ChangeRequest
from app.models.timetable import TimetableAssignment
from app.models.user import User
from app.services.changelog import log_change


router = APIRouter(prefix="/change-requests", tags=["change_requests"])


class ChangeRequestCreate(BaseModel):
    request_type: str
    run_id: Optional[int] = None
    assignment_id: Optional[int] = None
    activity_id: Optional[str] = None
    current_period_id: Optional[int] = None
    desired_period_id: Optional[int] = None
    current_room: Optional[str] = None
    desired_room: Optional[str] = None
    reason: Optional[str] = None


class ChangeRequestReview(BaseModel):
    approve: bool
    reviewer_notes: Optional[str] = None


class ChangeRequestOut(BaseModel):
    id: int
    requested_by: int
    run_id: Optional[int]
    assignment_id: Optional[int]
    activity_id: Optional[str]
    request_type: str
    current_period_id: Optional[int]
    desired_period_id: Optional[int]
    current_room: Optional[str]
    desired_room: Optional[str]
    reason: Optional[str]
    status: str
    reviewer_id: Optional[int]
    reviewer_notes: Optional[str]
    reviewed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("", response_model=ChangeRequestOut, status_code=201)
def create_request(
    body: ChangeRequestCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    req = ChangeRequest(
        requested_by=current.id,
        run_id=body.run_id,
        assignment_id=body.assignment_id,
        activity_id=body.activity_id,
        request_type=body.request_type,
        current_period_id=body.current_period_id,
        desired_period_id=body.desired_period_id,
        current_room=body.current_room,
        desired_room=body.desired_room,
        reason=body.reason,
        status="pending",
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    log_change(
        db, action="change_request_created", entity_type="change_request",
        entity_id=req.id, user_id=current.id, run_id=body.run_id,
        details={"type": body.request_type},
    )
    db.commit()
    return req


@router.get("", response_model=List[ChangeRequestOut])
def list_requests(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    stmt = select(ChangeRequest).order_by(ChangeRequest.created_at.desc())
    if current.role.value == "lecturer":
        stmt = stmt.where(ChangeRequest.requested_by == current.id)
    elif status:
        stmt = stmt.where(ChangeRequest.status == status)
    return list(db.scalars(stmt))


@router.post("/{req_id}/review", response_model=ChangeRequestOut)
def review_request(
    req_id: int,
    body: ChangeRequestReview,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    req = db.get(ChangeRequest, req_id)
    if not req:
        raise HTTPException(404, "Request not found")
    if req.status != "pending":
        raise HTTPException(400, "Request is already " + req.status)

    req.status = "approved" if body.approve else "rejected"
    req.reviewer_id = current.id
    req.reviewer_notes = body.reviewer_notes
    req.reviewed_at = datetime.utcnow()

    if body.approve and req.request_type == "move" and req.assignment_id and req.desired_period_id:
        assn = db.get(TimetableAssignment, req.assignment_id)
        if assn:
            old_period = assn.period_id
            old_room = assn.room_code
            assn.period_id = req.desired_period_id
            if req.desired_room:
                assn.room_code = req.desired_room
            assn.is_manual = True
            log_change(
                db, action="change_request_applied", entity_type="timetable_assignment",
                entity_id=assn.id, user_id=current.id, run_id=req.run_id,
                details={"from_period": old_period, "to_period": req.desired_period_id},
            )

    log_change(
        db, action="change_request_" + req.status, entity_type="change_request",
        entity_id=req.id, user_id=current.id, run_id=req.run_id,
    )
    db.commit()
    db.refresh(req)
    return req


@router.delete("/{req_id}")
def delete_request(
    req_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    req = db.get(ChangeRequest, req_id)
    if not req:
        raise HTTPException(404, "Request not found")
    if req.requested_by != current.id and current.role.value not in ("admin", "officer"):
        raise HTTPException(403, "Not allowed")
    if req.status != "pending":
        raise HTTPException(400, "Only pending requests can be deleted")
    db.delete(req)
    db.commit()
    return {"status": "deleted"}