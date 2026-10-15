"""Admin-only: link user accounts to cohorts / lecturers."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.models.cohort import Cohort
from app.models.lecturer import Lecturer
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/admin/link", tags=["admin_link"])


class LinkStudent(BaseModel):
    user_id: int
    cohort_id: str


class LinkLecturer(BaseModel):
    user_id: int
    lecturer_id: str


def _require_admin(user: User):
    if user.role.value not in ("admin", "officer"):
        raise HTTPException(status_code=403, detail="Admin only")


@router.get("/unlinked")
def list_unlinked(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    students = db.query(User).filter(User.role == "student", User.cohort_id == None).all()  # noqa
    lecturers = db.query(User).filter(User.role == "lecturer", User.lecturer_id == None).all()  # noqa
    return {
        "students": [{"id": u.id, "email": u.email, "full_name": u.full_name} for u in students],
        "lecturers": [{"id": u.id, "email": u.email, "full_name": u.full_name} for u in lecturers],
    }


@router.post("/student")
def link_student(payload: LinkStudent, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    u = db.query(User).filter(User.id == payload.user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    c = db.query(Cohort).filter(Cohort.id == payload.cohort_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Cohort not found")
    u.cohort_id = payload.cohort_id
    db.commit()
    return {"ok": True, "user_id": u.id, "cohort_id": u.cohort_id}


@router.post("/lecturer")
def link_lecturer(payload: LinkLecturer, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_admin(current_user)
    u = db.query(User).filter(User.id == payload.user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    l = db.query(Lecturer).filter(Lecturer.id == payload.lecturer_id).first()
    if not l:
        raise HTTPException(status_code=404, detail="Lecturer not found")
    u.lecturer_id = payload.lecturer_id
    db.commit()
    return {"ok": True, "user_id": u.id, "lecturer_id": u.lecturer_id}