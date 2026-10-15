"""Authentication endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import timedelta

from app.db.session import get_db
from app.core.security import verify_password, hash_password, create_access_token
from app.api.deps import get_current_user, require_admin
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, TokenResponse, UserOut, UserCreate, UserUpdate
from app.schemas.common import Message
from app.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == body.email))
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Account is inactive")
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        subject=user.id,
        expires_delta=expires,
        extra={"email": user.email, "role": user.role.value},
    )
    return TokenResponse(access_token=token, token_type="bearer", expires_in=int(expires.total_seconds()))


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return list(db.scalars(select(User).order_by(User.id)))


@router.post("/users", response_model=UserOut, status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    existing = db.scalar(select(User).where(User.email == body.email))
    if existing:
        raise HTTPException(400, "Email already registered")
    try:
        role = UserRole(body.role)
    except ValueError:
        raise HTTPException(400, f"Invalid role: {body.role}")
    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        role=role,
        cohort_id=body.cohort_id,
        lecturer_id=body.lecturer_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    data = body.model_dump(exclude_unset=True)
    if "password" in data and data["password"]:
        user.hashed_password = hash_password(data.pop("password"))
    if "role" in data and data["role"]:
        try:
            user.role = UserRole(data.pop("role"))
        except ValueError:
            raise HTTPException(400, "Invalid role")
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}", response_model=Message)
def delete_user(user_id: int, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    if user_id == current.id:
        raise HTTPException(400, "Cannot delete yourself")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    db.delete(user)
    db.commit()
    return Message(detail="User deleted")