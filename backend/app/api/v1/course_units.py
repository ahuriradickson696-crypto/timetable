"""CourseUnit CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.session import get_db
from app.api.deps import get_current_user, require_officer
from app.models.course_unit import CourseUnit, CourseUnitProgramme
from app.models.programme import Programme
from app.models.user import User
from app.schemas.course_unit import CourseUnitCreate, CourseUnitUpdate, CourseUnitOut
from app.schemas.common import Message


router = APIRouter(prefix="/course-units", tags=["course_units"])


@router.get("", response_model=list[CourseUnitOut])
def list_course_units(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return list(db.scalars(select(CourseUnit).order_by(CourseUnit.code)))


@router.get("/{code}", response_model=CourseUnitOut)
def get_course_unit(
    code: str,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    obj = db.get(CourseUnit, code)
    if not obj:
        raise HTTPException(404, "Course unit not found")
    return obj


@router.post("", response_model=CourseUnitOut, status_code=201)
def create_course_unit(
    body: CourseUnitCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    if db.get(CourseUnit, body.code):
        raise HTTPException(400, f"Course unit {body.code} already exists")
    data = body.model_dump(exclude={"shared_across_programmes"})
    obj = CourseUnit(**data)
    db.add(obj)
    db.flush()
    for prog_code in body.shared_across_programmes:
        if db.get(Programme, prog_code):
            db.add(CourseUnitProgramme(course_unit_code=obj.code, programme_code=prog_code))
    db.commit()
    db.refresh(obj)
    return obj


@router.patch("/{code}", response_model=CourseUnitOut)
def update_course_unit(
    code: str,
    body: CourseUnitUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    obj = db.get(CourseUnit, code)
    if not obj:
        raise HTTPException(404, "Course unit not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{code}", response_model=Message)
def delete_course_unit(
    code: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    obj = db.get(CourseUnit, code)
    if not obj:
        raise HTTPException(404, "Course unit not found")
    db.delete(obj)
    db.commit()
    return Message(detail=f"Course unit {code} deleted")
