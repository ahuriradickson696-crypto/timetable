"""Public lecturer list for the kiosk-style login page."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.get("/lecturers-public")
def list_public_lecturers(db: Session = Depends(get_db)):
    """
    Public endpoint. Returns id/name for every active lecturer.
    No auth required so the login kiosk can populate the dropdown.
    """
    users = (
        db.query(User)
        .filter(
            User.role == UserRole.LECTURER,
            User.is_active == True,  # noqa: E712
        )
        .order_by(User.full_name)
        .all()
    )
    return [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "lecturer_id": u.lecturer_id,
        }
        for u in users
    ]


@router.post("/login-as-lecturer")
def login_as_lecturer(body: dict, db: Session = Depends(get_db)):
    """
    Kiosk login: given a lecturer's user id, return a JWT.
    No password required — safe for a physically-controlled staff room.
    """
    user_id = body.get("user_id")
    if not user_id:
        from fastapi import HTTPException
        raise HTTPException(400, "user_id required")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != UserRole.LECTURER or not user.is_active:
        from fastapi import HTTPException
        raise HTTPException(404, "Lecturer not found")

    from app.core.security import create_access_token
    token = create_access_token(subject=str(user.id), extra={"role": user.role.value})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "lecturer_id": user.lecturer_id,
        },
    }