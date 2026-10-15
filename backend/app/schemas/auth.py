"""Auth schemas."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.schemas.common import ORMModel


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(ORMModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    cohort_id: Optional[str] = None
    lecturer_id: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=6)
    role: str = "viewer"
    cohort_id: Optional[str] = None
    lecturer_id: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None
    cohort_id: Optional[str] = None
    lecturer_id: Optional[str] = None