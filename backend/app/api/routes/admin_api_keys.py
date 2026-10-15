"""Admin API key management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import secrets

from app.db.session import get_db
from app.models.user import User
from app.models.api_key import APIKey
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/admin/api-keys", tags=["admin-api-keys"])


class CreateKeyReq(BaseModel):
    name: str
    notes: Optional[str] = None


@router.get("")
def list_keys(db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if current.role.value not in ("admin", "officer"):
        raise HTTPException(403, "Admin only")
    return [
        {
            "id": k.id,
            "name": k.name,
            "key": k.key[:12] + "..." + k.key[-4:],
            "active": k.active,
            "call_count": k.call_count,
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "created_at": k.created_at.isoformat() if k.created_at else None,
            "notes": k.notes,
        }
        for k in db.query(APIKey).order_by(APIKey.id.desc()).all()
    ]


@router.post("")
def create_key(body: CreateKeyReq, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if current.role.value not in ("admin", "officer"):
        raise HTTPException(403, "Admin only")
    token = "aviu_" + secrets.token_urlsafe(32)
    k = APIKey(
        name=body.name.strip(),
        key=token,
        active=True,
        created_by=current.id,
        notes=body.notes,
    )
    db.add(k)
    db.commit()
    db.refresh(k)
    return {"id": k.id, "name": k.name, "key": k.key, "message": "Save this key — it will not be shown again in full."}


@router.post("/{key_id}/revoke")
def revoke_key(key_id: int, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if current.role.value not in ("admin", "officer"):
        raise HTTPException(403, "Admin only")
    k = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not k:
        raise HTTPException(404, "Key not found")
    k.active = False
    db.commit()
    return {"ok": True, "id": k.id, "active": k.active}