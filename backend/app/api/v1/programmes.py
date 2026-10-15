"""Programme CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user, require_officer
from app.models.programme import Programme
from app.models.user import User
from app.schemas.programme import ProgrammeCreate, ProgrammeUpdate, ProgrammeOut
from app.schemas.common import Message


router = APIRouter(prefix="/programmes", tags=["programmes"])


@router.get("", response_model=list[ProgrammeOut])
def list_programmes(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return list(db.scalars(select(Programme).order_by(Programme.code)))


@router.get("/{code}", response_model=ProgrammeOut)
def get_programme(
    code: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    obj = db.get(Programme, code)
    if not obj:
        raise HTTPException(404, "Programme not found")
    return obj


@router.post("", response_model=ProgrammeOut, status_code=201)
def create_programme(
    body: ProgrammeCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    if db.get(Programme, body.code):
        raise HTTPException(400, f"Programme {body.code} already exists")
    obj = Programme(**body.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/{code}", response_model=ProgrammeOut)
def update_programme(
    code: str,
    body: ProgrammeUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    obj = db.get(Programme, code)
    if not obj:
        raise HTTPException(404, "Programme not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{code}", response_model=Message)
def delete_programme(
    code: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    obj = db.get(Programme, code)
    if not obj:
        raise HTTPException(404, "Programme not found")
    db.delete(obj)
    db.commit()
    return Message(detail=f"Programme {code} deleted")
