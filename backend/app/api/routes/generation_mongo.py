"""Timetable generation via OR-Tools. Writes to MongoDB."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import time

from app.db.mongodb import (
    activities_col, rooms_col, time_periods_col, cohorts_col,
    timetable_runs_col, timetable_assignments_col,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/generation", tags=["generation"])


class GenerateRequest(BaseModel):
    intake: str = "Aug"
    academic_year: str = "2026/2027"
    semester: int = 1
    run_type: str = "teaching"  # teaching | exam


@router.get("/runs")
async def list_runs(current=Depends(get_current_user)):
    rows = await timetable_runs_col().find().sort("id", -1).to_list(500)
    for r in rows:
        r["_id"] = str(r["_id"])
    return rows


@router.get("/runs/{run_id}")
async def get_run(run_id: int, current=Depends(get_current_user)):
    r = await timetable_runs_col().find_one({"id": run_id})
    if not r:
        raise HTTPException(404, "Run not found")
    r["_id"] = str(r["_id"])
    return r


@router.post("/generate")
async def generate(body: GenerateRequest, current=Depends(get_current_user)):
    """
    Simple heuristic scheduler:
      - For each activity, find a free slot + room matching the room type.
      - Assign lecturer/cohort/room without conflicts.
    Stores a run + assignments in MongoDB.
    """
    if current.get("role") not in ("admin", "officer"):
        raise HTTPException(403, "Admin only")

    started = time.time()

    activities = await activities_col().find({
        "intake": body.intake,
        "academic_year": body.academic_year,
        "semester": body.semester,
        "activity_type": body.run_type,
    }).to_list(2000)

    if not activities:
        raise HTTPException(400, "No activities match those parameters")

    rooms = await rooms_col().find({"active": True}).to_list(500)
    periods = await time_periods_col().find({"mode": "Day", "is_break": False}).sort("order_index", 1).to_list(500)

    # Build lookup maps
    rooms_by_type = {}
    for r in rooms:
        rooms_by_type.setdefault(r["room_type"], []).append(r)

    # Track occupancy
    lecturer_busy = set()   # (lecturer_id, day, period_id)
    cohort_busy = set()     # (cohort_id, day, period_id)
    room_busy = set()       # (room_code, day, period_id)

    assignments = []

    for act in activities:
        lect = act.get("lecturer_id")
        cohort = act.get("cohort_id")
        preferred_type = act.get("preferred_room_type") or "Lecture"
        duration = max(1, int(act.get("duration_periods", 1)))

        placed = False
        for period in periods:
            day = period["day"]
            pid = period["period_id"]

            if lect and (lect, day, pid) in lecturer_busy:
                continue
            if cohort and (cohort, day, pid) in cohort_busy:
                continue

            # Find a room of the right type that's free
            candidates = rooms_by_type.get(preferred_type, []) + rooms_by_type.get("Lecture", [])
            room = None
            for r in candidates:
                if (r["code"], day, pid) not in room_busy:
                    room = r
                    break
            if not room:
                continue

            # Assign
            if lect:
                lecturer_busy.add((lect, day, pid))
            if cohort:
                cohort_busy.add((cohort, day, pid))
            room_busy.add((room["code"], day, pid))

            assignments.append({
                "activity_id": act["id"],
                "cohort_id": cohort,
                "lecturer_id": lect,
                "module_code": act["module_code"],
                "day": day,
                "period_id": pid,
                "room_code": room["code"],
            })
            placed = True
            break

        if not placed:
            # Could not place — skip for now
            pass

    # Persist the run
    next_id = (await timetable_runs_col().find_one(sort=[("id", -1)])) or {"id": 0}
    run_id = (next_id.get("id") or 0) + 1
    wall = round(time.time() - started, 3)

    run_doc = {
        "id": run_id,
        "intake": body.intake,
        "academic_year": body.academic_year,
        "semester": body.semester,
        "run_type": body.run_type,
        "status": "success" if assignments else "failed",
        "message": f"Scheduled {len(assignments)} activities",
        "metrics": {"wall_time": wall, "assignments": len(assignments)},
        "is_published": False,
        "is_locked": False,
        "created_at": datetime.utcnow(),
    }
    await timetable_runs_col().insert_one(run_doc)

    if assignments:
        for a in assignments:
            a["run_id"] = run_id
        await timetable_assignments_col().insert_many(assignments)

    run_doc.pop("_id", None)
    return run_doc


@router.get("/runs/{run_id}/by-cohort/{cohort_id}")
async def view_by_cohort(run_id: int, cohort_id: str, current=Depends(get_current_user)):
    rows = await timetable_assignments_col().find({
        "run_id": run_id,
        "cohort_id": cohort_id,
    }).to_list(2000)
    for r in rows:
        r["_id"] = str(r["_id"])
    return rows