"""Activity CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user, require_officer
from app.models.activity import Activity
from app.models.cohort import Cohort
from app.models.course_unit import CourseUnit
from app.models.lecturer import Lecturer
from app.models.user import User
from app.schemas.activity import ActivityCreate, ActivityUpdate, ActivityOut
from app.schemas.common import Message


router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("", response_model=list[ActivityOut])
def list_activities(
    activity_type: str | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    stmt = select(Activity).order_by(Activity.id)
    if activity_type:
        stmt = stmt.where(Activity.activity_type == activity_type)
    return list(db.scalars(stmt))


@router.get("/{activity_id}", response_model=ActivityOut)
def get_activity(
    activity_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    obj = db.get(Activity, activity_id)
    if not obj:
        raise HTTPException(404, "Activity not found")
    return obj


@router.post("", response_model=ActivityOut, status_code=201)
def create_activity(
    body: ActivityCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    if db.get(Activity, body.id):
        raise HTTPException(400, f"Activity {body.id} already exists")
    if not db.get(Cohort, body.cohort_id):
        raise HTTPException(400, f"Cohort {body.cohort_id} not found")
    if not db.get(CourseUnit, body.module_code):
        raise HTTPException(400, f"Course unit {body.module_code} not found")
    if not db.get(Lecturer, body.lecturer_id):
        raise HTTPException(400, f"Lecturer {body.lecturer_id} not found")
    obj = Activity(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/{activity_id}", response_model=ActivityOut)
def update_activity(
    activity_id: str,
    body: ActivityUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    obj = db.get(Activity, activity_id)
    if not obj:
        raise HTTPException(404, "Activity not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{activity_id}", response_model=Message)
def delete_activity(
    activity_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    obj = db.get(Activity, activity_id)
    if not obj:
        raise HTTPException(404, "Activity not found")
    db.delete(obj)
    db.commit()
    return Message(detail=f"Activity {activity_id} deleted")