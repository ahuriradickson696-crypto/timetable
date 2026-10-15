"""Publish / unpublish timetable runs. MongoDB."""
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime

from app.db.mongodb import timetable_runs_col
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/publishing", tags=["publishing"])


@router.post("/runs/{run_id}/publish")
async def publish(run_id: int, current=Depends(get_current_user)):
    if current.get("role") not in ("admin", "officer"):
        raise HTTPException(403, "Admin only")
    r = await timetable_runs_col().find_one({"id": run_id})
    if not r:
        raise HTTPException(404, "Run not found")
    await timetable_runs_col().update_one(
        {"id": run_id},
        {"$set": {"is_published": True, "published_at": datetime.utcnow()}},
    )
    return {"ok": True, "run_id": run_id, "is_published": True}


@router.post("/runs/{run_id}/unpublish")
async def unpublish(run_id: int, current=Depends(get_current_user)):
    if current.get("role") not in ("admin", "officer"):
        raise HTTPException(403, "Admin only")
    await timetable_runs_col().update_one(
        {"id": run_id},
        {"$set": {"is_published": False, "published_at": None}},
    )
    return {"ok": True, "run_id": run_id, "is_published": False}


@router.get("/runs/published")
async def list_published(current=Depends(get_current_user)):
    rows = await timetable_runs_col().find({"is_published": True}).sort("id", -1).to_list(50)
    for r in rows:
        r["_id"] = str(r["_id"])
    return rows