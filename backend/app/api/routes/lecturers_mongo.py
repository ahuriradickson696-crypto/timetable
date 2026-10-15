"""Lecturers — MongoDB."""
from fastapi import APIRouter, Depends
from app.db.mongodb import lecturers_col
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/lecturers", tags=["lecturers"])


@router.get("")
async def list_lecturers(current=Depends(get_current_user)):
    rows = await lecturers_col().find().sort("id", 1).to_list(500)
    for r in rows:
        r["_id"] = str(r["_id"])
    return rows


@router.get("/{lecturer_id}")
async def get_lecturer(lecturer_id: str, current=Depends(get_current_user)):
    r = await lecturers_col().find_one({"id": lecturer_id})
    if r:
        r["_id"] = str(r["_id"])
    return r or {}