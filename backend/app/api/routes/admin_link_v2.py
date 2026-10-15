"""Admin helper: link a student to a cohort."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.cohort import Cohort
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/admin/link", tags=["admin_link"])


class LinkStudentReq(BaseModel):
    email: str
    cohort_id: str


@router.post("/student-to-cohort")
def link_student_to_cohort(
    body: LinkStudentReq,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    if current.role not in (UserRole.ADMIN, UserRole.OFFICER):
        raise HTTPException(403, "Admin only")
    user = db.query(User).filter(User.email == body.email.lower()).first()
    if not user:
        raise HTTPException(404, "User not found: " + body.email)
    cohort = db.query(Cohort).filter(Cohort.id == body.cohort_id).first()
    if not cohort:
        raise HTTPException(404, "Cohort not found: " + body.cohort_id)
    user.cohort_id = body.cohort_id
    db.commit()
    return {"ok": True, "email": user.email, "cohort_id": user.cohort_id}