"""Lecturer CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user, require_officer
from app.models.lecturer import Lecturer, LecturerModule
from app.models.course_unit import CourseUnit
from app.models.user import User
from app.schemas.lecturer import LecturerCreate, LecturerUpdate, LecturerOut
from app.schemas.common import Message


router = APIRouter(prefix="/lecturers", tags=["lecturers"])


@router.get("", response_model=list[LecturerOut])
def list_lecturers(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return list(db.scalars(select(Lecturer).order_by(Lecturer.id)))


@router.get("/{lecturer_id}", response_model=LecturerOut)
def get_lecturer(
    lecturer_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    obj = db.get(Lecturer, lecturer_id)
    if not obj:
        raise HTTPException(404, "Lecturer not found")
    return obj


@router.post("", response_model=LecturerOut, status_code=201)
def create_lecturer(
    body: LecturerCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    if db.get(Lecturer, body.id):
        raise HTTPException(400, f"Lecturer {body.id} already exists")
    data = body.model_dump(exclude={"can_teach_modules"})
    obj = Lecturer(**data)
    db.add(obj)
    db.flush()
    for code in body.can_teach_modules:
        if db.get(CourseUnit, code):
            db.add(LecturerModule(lecturer_id=obj.id, course_unit_code=code))
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/{lecturer_id}", response_model=LecturerOut)
def update_lecturer(
    lecturer_id: str,
    body: LecturerUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    obj = db.get(Lecturer, lecturer_id)
    if not obj:
        raise HTTPException(404, "Lecturer not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{lecturer_id}", response_model=Message)
def delete_lecturer(
    lecturer_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    obj = db.get(Lecturer, lecturer_id)
    if not obj:
        raise HTTPException(404, "Lecturer not found")
    db.delete(obj)
    db.commit()
    return Message(detail=f"Lecturer {lecturer_id} deleted")
