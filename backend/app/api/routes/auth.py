"""Auth endpoints — MongoDB version."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from bson import ObjectId

from app.db.mongodb import users_col
from app.db.mongodb import users_col, lecturers_col
from app.core.security import hash_password, verify_password, create_access_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(..., description="STUDENT or LECTURER")


def _user_public(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "email": doc["email"],
        "full_name": doc["full_name"],
        "role": doc.get("role", "viewer"),
        "is_active": doc.get("is_active", True),
        "cohort_id": doc.get("cohort_id"),
        "lecturer_id": doc.get("lecturer_id"),
    }


@router.post("/login")
async def login(body: LoginRequest):
    doc = await users_col().find_one({"email": body.email.lower()})
    if not doc or not verify_password(body.password, doc["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not doc.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account disabled")
    token = create_access_token(subject=str(doc["_id"]), extra={"role": doc.get("role", "viewer")})
    return {"access_token": token, "token_type": "bearer", "expires_in": 86400}


@router.get("/me")
async def me(current: dict = Depends(get_current_user)):
    return _user_public(current)


@router.post("/signup", status_code=201)
async def signup(body: SignupRequest):
    role_upper = body.role.upper().strip()
    if role_upper not in ("STUDENT", "LECTURER"):
        raise HTTPException(400, "Role must be STUDENT or LECTURER")

    email = body.email.lower()
    if await users_col().find_one({"email": email}):
        raise HTTPException(409, "Email already registered")

    # Auto-link lecturer: try to match by full_name (case-insensitive) first,
    # else by email if the lecturer record has one.
    lecturer_id = None
    if role_upper == "LECTURER":
        match = await lecturers_col().find_one({
            "full_name": {"$regex": "^" + body.full_name.strip() + "$", "$options": "i"}
        })
        if not match:
            match = await lecturers_col().find_one({"email": email})
        if match:
            lecturer_id = match["id"]

    doc = {
        "email": email,
        "full_name": body.full_name.strip(),
        "hashed_password": hash_password(body.password),
        "role": role_upper.lower(),
        "is_active": True,
        "cohort_id": None,
        "lecturer_id": lecturer_id,
        "created_at": datetime.utcnow(),
    }
    result = await users_col().insert_one(doc)
    doc["_id"] = result.inserted_id
    token = create_access_token(subject=str(doc["_id"]), extra={"role": doc["role"]})
    return {"access_token": token, "token_type": "bearer", "user": _user_public(doc)}