"""Student/Lecturer portal — MongoDB."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime

from app.db.mongodb import (
    users_col, cohorts_col, activities_col, enrollments_col,
    timetable_runs_col, timetable_assignments_col,
    course_units_col, lecturers_col, rooms_col, time_periods_col,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/portal", tags=["portal"])


async def _published_run():
    return await timetable_runs_col().find_one(
        {"is_published": True}, sort=[("id", -1)]
    )


@router.get("/me")
async def portal_me(current=Depends(get_current_user)):
    return {
        "id": current["_id"],
        "email": current.get("email"),
        "full_name": current.get("full_name"),
        "role": current.get("role"),
        "cohort_id": current.get("cohort_id"),
        "lecturer_id": current.get("lecturer_id"),
    }


async def _my_cells(current: dict):
    run = await _published_run()
    if not run:
        return []

    q = {}
    if current.get("role") == "student":
        if not current.get("cohort_id"):
            return []
        q["cohort_id"] = current["cohort_id"]
    elif current.get("role") == "lecturer":
        if not current.get("lecturer_id"):
            return []
        q["lecturer_id"] = current["lecturer_id"]
    else:
        return []

    assignments = await timetable_assignments_col().find({"run_id": run["id"]}).to_list(2000)
    activities = {a["id"]: a for a in await activities_col().find(q).to_list(2000) if a.get("id")}
    act_ids = set(activities.keys())

    period_lookup = {p["period_id"]: p for p in await time_periods_col().find().to_list(500)}
    cu_lookup = {c["code"]: c for c in await course_units_col().find().to_list(2000)}
    lect_lookup = {l["id"]: l for l in await lecturers_col().find().to_list(500)}
    room_lookup = {r["code"]: r for r in await rooms_col().find().to_list(500)}

    cells = []
    for a in assignments:
        if a["activity_id"] not in act_ids:
            continue
        act = activities[a["activity_id"]]
        tp = period_lookup.get(a.get("period_id"), {})
        cu = cu_lookup.get(act["module_code"], {})
        lect = lect_lookup.get(act.get("lecturer_id"), {})
        room = room_lookup.get(a.get("room_code"), {})
        cells.append({
            "day": tp.get("day"),
            "period_id": a.get("period_id"),
            "start_time": tp.get("start_time"),
            "end_time": tp.get("end_time"),
            "module_code": act["module_code"],
            "module_name": cu.get("name"),
            "cohort_id": act.get("cohort_id"),
            "lecturer_id": act.get("lecturer_id"),
            "lecturer_name": lect.get("full_name"),
            "room_code": a.get("room_code"),
            "room_name": room.get("name"),
            "activity_type": act.get("activity_type"),
        })
    return cells


@router.get("/my-timetable")
async def my_timetable(current=Depends(get_current_user)):
    return await _my_cells(current)


@router.get("/my-next-class")
async def my_next_class(current=Depends(get_current_user)):
    cells = await _my_cells(current)
    if not cells:
        return {"next": None, "message": "No classes scheduled"}
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    today = datetime.now().strftime("%A")
    today_idx = order.index(today) if today in order else 0
    cells.sort(key=lambda c: (order.index(c["day"]) if c.get("day") in order else 99, c.get("start_time") or "99:99"))
    for c in cells:
        d = order.index(c["day"]) if c.get("day") in order else 99
        if d > today_idx:
            return c
        if d == today_idx:
            return c
    return cells[0]


@router.get("/my-today")
async def my_today(current=Depends(get_current_user)):
    cells = await _my_cells(current)
    today = datetime.now().strftime("%A")
    return {"day": today, "classes": [c for c in cells if c.get("day") == today]}


@router.get("/my-exams")
async def my_exams(current=Depends(get_current_user)):
    return {"exam": [], "test": []}