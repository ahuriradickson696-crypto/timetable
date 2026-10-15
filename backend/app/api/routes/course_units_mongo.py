"""Course Units — MongoDB."""
from fastapi import APIRouter, Depends
from app.db.mongodb import course_units_col
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/course-units", tags=["course_units"])


@router.get("")
async def list_units(current=Depends(get_current_user)):
    rows = await course_units_col().find().sort("code", 1).to_list(1000)
    for r in rows:
        r["_id"] = str(r["_id"])
    return rows


@router.get("/{code}")
async def get_unit(code: str, current=Depends(get_current_user)):
    r = await course_units_col().find_one({"code": code})
    if r:
        r["_id"] = str(r["_id"])
    return r or {}