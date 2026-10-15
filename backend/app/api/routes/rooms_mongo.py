"""Rooms — MongoDB."""
from fastapi import APIRouter, Depends
from app.db.mongodb import rooms_col
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/rooms", tags=["rooms"])


@router.get("")
async def list_rooms(current=Depends(get_current_user)):
    rows = await rooms_col().find().sort("code", 1).to_list(500)
    for r in rows:
        r["_id"] = str(r["_id"])
    return rows