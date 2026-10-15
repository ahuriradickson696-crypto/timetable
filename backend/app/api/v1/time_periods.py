"""TimePeriod CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user, require_officer
from app.models.time_period import TimePeriod
from app.models.user import User
from app.schemas.time_period import TimePeriodCreate, TimePeriodUpdate, TimePeriodOut
from app.schemas.common import Message


router = APIRouter(prefix="/time-periods", tags=["time_periods"])


@router.get("", response_model=list[TimePeriodOut])
def list_periods(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return list(db.scalars(select(TimePeriod).order_by(TimePeriod.mode, TimePeriod.day, TimePeriod.order_index)))


@router.post("", response_model=TimePeriodOut, status_code=201)
def create_period(
    body: TimePeriodCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    obj = TimePeriod(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/{period_id}", response_model=TimePeriodOut)
def update_period(
    period_id: int,
    body: TimePeriodUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    obj = db.get(TimePeriod, period_id)
    if not obj:
        raise HTTPException(404, "Period not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{period_id}", response_model=Message)
def delete_period(
    period_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    obj = db.get(TimePeriod, period_id)
    if not obj:
        raise HTTPException(404, "Period not found")
    db.delete(obj)
    db.commit()
    return Message(detail=f"Period {period_id} deleted")
