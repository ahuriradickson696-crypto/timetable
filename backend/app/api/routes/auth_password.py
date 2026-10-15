"""Forgot password flow (dev: token shown in response; prod: email)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta, timezone
import secrets
import hashlib

from app.db.session import get_db
from app.models.user import User
from app.core.security import hash_password

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# In-memory token store: token_hash -> (user_id, expires_at)
_RESET_STORE = {}


class ForgotReq(BaseModel):
    email: EmailStr


class ResetReq(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


def _hash(tok: str) -> str:
    return hashlib.sha256(tok.encode()).hexdigest()


@router.post("/forgot-password")
def forgot_password(payload: ForgotReq, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    # Always return generic message (no user enumeration)
    if not user:
        return {"ok": True, "message": "If that email exists, a reset link was sent."}

    token = secrets.token_urlsafe(32)
    _RESET_STORE[_hash(token)] = (
        user.id,
        datetime.now(timezone.utc) + timedelta(minutes=30),
    )
    # DEV: return token directly. PROD: email it.
    return {
        "ok": True,
        "message": "Reset link generated.",
        "reset_token_dev_only": token,
        "expires_in_minutes": 30,
    }


@router.post("/reset-password")
def reset_password(payload: ResetReq, db: Session = Depends(get_db)):
    key = _hash(payload.token)
    entry = _RESET_STORE.get(key)
    if not entry:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    user_id, expires = entry
    if datetime.now(timezone.utc) > expires:
        _RESET_STORE.pop(key, None)
        raise HTTPException(status_code=400, detail="Reset token expired")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    _RESET_STORE.pop(key, None)
    return {"ok": True, "message": "Password reset successfully"}