"""Public self-signup for students and lecturers. Auto-links lecturer records."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.lecturer import Lecturer
from app.core.security import hash_password, create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(..., description="STUDENT or LECTURER only")


class SignupResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/signup", response_model=SignupResponse, status_code=201)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    role_upper = payload.role.upper().strip()
    if role_upper not in ("STUDENT", "LECTURER"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be STUDENT or LECTURER. Admin accounts are created by administrators.",
        )

    email_lower = payload.email.lower()
    existing = db.query(User).filter(User.email == email_lower).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Try signing in instead.",
        )

    # Auto-link lecturer if a matching Lecturer record exists (by full_name or email note)
    lecturer_id = None
    if role_upper == "LECTURER":
        match = db.query(Lecturer).filter(Lecturer.full_name.ilike(payload.full_name.strip())).first()
        if match:
            lecturer_id = match.id

    user = User(
        email=email_lower,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
        role=UserRole.STUDENT if role_upper == "STUDENT" else UserRole.LECTURER,
        is_active=True,
        lecturer_id=lecturer_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id), extra={"role": user.role.value})

    return SignupResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role.value,
            "is_active": user.is_active,
            "lecturer_id": user.lecturer_id,
        },
    )