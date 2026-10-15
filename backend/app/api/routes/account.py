"""Self-service account endpoints: profile, GDPR export, delete."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import json
from datetime import datetime

from app.db.session import get_db
from app.models.user import User
from app.models.activity import Activity
from app.core.security import hash_password, verify_password
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/account", tags=["account"])


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value,
        "is_active": current_user.is_active,
        "cohort_id": current_user.cohort_id,
        "lecturer_id": current_user.lecturer_id,
    }


@router.patch("/me")
def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.full_name:
        current_user.full_name = payload.full_name.strip()
    if payload.email:
        new_email = payload.email.lower()
        if new_email != current_user.email:
            existing = db.query(User).filter(User.email == new_email).first()
            if existing:
                raise HTTPException(status_code=409, detail="Email already in use")
            current_user.email = new_email
    db.commit()
    return {"ok": True, "email": current_user.email, "full_name": current_user.full_name}


@router.post("/change-password")
def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"ok": True, "message": "Password changed"}


@router.get("/export")
def export_my_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """GDPR data portability — download everything we hold about you."""
    activities = []
    if current_user.cohort_id:
        rows = db.query(Activity).filter(Activity.cohort_id == current_user.cohort_id).all()
        activities = [
            {
                "id": a.id,
                "module_code": a.module_code,
                "cohort_id": a.cohort_id,
                "activity_type": a.activity_type,
            }
            for a in rows
        ]

    payload = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "account": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role.value,
            "is_active": current_user.is_active,
            "cohort_id": current_user.cohort_id,
            "lecturer_id": current_user.lecturer_id,
            "created_at": getattr(current_user, "created_at", None).isoformat() if getattr(current_user, "created_at", None) else None,
        },
        "activities": activities,
    }
    return payload


@router.delete("/me")
def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft delete: deactivate + anonymize. Keeps referential integrity."""
    current_user.is_active = False
    current_user.email = "deleted+" + str(current_user.id) + "@deleted.local"
    current_user.full_name = "Deleted User"
    current_user.cohort_id = None
    current_user.lecturer_id = None
    db.commit()
    return {"ok": True, "message": "Account deactivated and anonymized"}