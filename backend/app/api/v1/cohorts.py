"""Cohort CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user, require_officer
from app.models.cohort import Cohort
from app.models.programme import Programme
from app.models.user import User
from app.schemas.cohort import CohortCreate, CohortUpdate, CohortOut
from app.schemas.common import Message


router = APIRouter(prefix="/cohorts", tags=["cohorts"])


@router.get("", response_model=list[CohortOut])
def list_cohorts(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return list(db.scalars(select(Cohort).order_by(Cohort.id)))


@router.get("/{cohort_id}", response_model=CohortOut)
def get_cohort(
    cohort_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    obj = db.get(Cohort, cohort_id)
    if not obj:
        raise HTTPException(404, "Cohort not found")
    return obj


@router.post("", response_model=CohortOut, status_code=201)
def create_cohort(
    body: CohortCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    if db.get(Cohort, body.id):
        raise HTTPException(400, f"Cohort {body.id} already exists")
    if not db.get(Programme, body.programme_code):
        raise HTTPException(400, f"Programme {body.programme_code} not found")
    obj = Cohort(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/{cohort_id}", response_model=CohortOut)
def update_cohort(
    cohort_id: str,
    body: CohortUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    obj = db.get(Cohort, cohort_id)
    if not obj:
        raise HTTPException(404, "Cohort not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{cohort_id}", response_model=Message)
def delete_cohort(
    cohort_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    obj = db.get(Cohort, cohort_id)
    if not obj:
        raise HTTPException(404, "Cohort not found")
    db.delete(obj)
    db.commit()
    return Message(detail=f"Cohort {cohort_id} deleted")
