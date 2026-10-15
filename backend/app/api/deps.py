"""Shared FastAPI dependencies (Mongo version)."""
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from typing import Optional
from bson import ObjectId

from app.core.security import decode_access_token
from app.db.mongodb import users_col

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def _load_user_from_token(token: str):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    try:
        user_id = ObjectId(payload["sub"])
    except Exception:
        return None
    doc = await users_col().find_one({"_id": user_id})
    if not doc or not doc.get("is_active", True):
        return None
    doc["_id"] = str(doc["_id"])
    doc["role"] = doc.get("role", "viewer")
    return doc


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)) -> dict:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await _load_user_from_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[dict]:
    if not token:
        return None
    return await _load_user_from_token(token)


def require_role(*allowed: str):
    async def _checker(current: dict = Depends(get_current_user)) -> dict:
        if current.get("role") not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {current.get('role')} not permitted",
            )
        return current
    return _checker