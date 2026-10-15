"""Admin API keys (MongoDB)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import secrets
from datetime import datetime

from app.db.mongodb import api_keys_col
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/admin/api-keys", tags=["admin-api-keys"])


class CreateKeyReq(BaseModel):
    name: str
    notes: Optional[str] = None


@router.get("")
async def list_keys(current=Depends(get_current_user)):
    if current.get("role") not in ("admin", "officer"):
        raise HTTPException(403, "Admin only")
    rows = await api_keys_col().find().sort("_id", -1).to_list(200)
    return [
        {
            "id": str(k["_id"]),
            "name": k["name"],
            "key": k["key"][:12] + "..." + k["key"][-4:],
            "active": k.get("active", True),
            "call_count": k.get("call_count", 0),
            "last_used_at": k.get("last_used_at").isoformat() if k.get("last_used_at") else None,
            "created_at": k.get("created_at").isoformat() if k.get("created_at") else None,
            "notes": k.get("notes"),
        }
        for k in rows
    ]


@router.post("")
async def create_key(body: CreateKeyReq, current=Depends(get_current_user)):
    if current.get("role") not in ("admin", "officer"):
        raise HTTPException(403, "Admin only")
    token = "aviu_" + secrets.token_urlsafe(32)
    doc = {
        "name": body.name.strip(),
        "key": token,
        "active": True,
        "created_by": current["_id"],
        "notes": body.notes,
        "call_count": 0,
        "last_used_at": None,
        "created_at": datetime.utcnow(),
    }
    result = await api_keys_col().insert_one(doc)
    return {
        "id": str(result.inserted_id),
        "name": doc["name"],
        "key": token,
        "message": "Save this key — it will not be shown again in full.",
    }


@router.post("/{key_id}/revoke")
async def revoke_key(key_id: str, current=Depends(get_current_user)):
    if current.get("role") not in ("admin", "officer"):
        raise HTTPException(403, "Admin only")
    from bson import ObjectId
    try:
        oid = ObjectId(key_id)
    except Exception:
        raise HTTPException(400, "Invalid key id")
    r = await api_keys_col().update_one({"_id": oid}, {"$set": {"active": False}})
    if r.matched_count == 0:
        raise HTTPException(404, "Key not found")
    return {"ok": True, "id": key_id, "active": False}