"""Notification endpoints: track last seen published run per user."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.models.timetable import TimetableRun
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


def _latest_published(db: Session) -> Optional[int]:
    """Return the id of the most recently published run, or None."""
    row = (
        db.query(TimetableRun)
        .filter(TimetableRun.is_published == True)
        .order_by(TimetableRun.published_at.desc())
        .first()
    )
    return row.id if row else None


@router.get("/me")
def my_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return whether the user has unread timetable updates.
    Uses user.last_seen_run_id (int, nullable) compared to the latest published run.
    """
    latest = _latest_published(db)
    seen = getattr(current_user, "last_seen_run_id", None)
    has_new = bool(latest and (seen is None or latest > seen))
    return {
        "latest_published_run_id": latest,
        "last_seen_run_id": seen,
        "has_new_timetable": has_new,
    }


@router.post("/mark-seen")
def mark_seen(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear the badge by marking the latest published run as seen."""
    latest = _latest_published(db)
    if latest:
        current_user.last_seen_run_id = latest
        db.commit()
    return {"ok": True, "last_seen_run_id": latest}