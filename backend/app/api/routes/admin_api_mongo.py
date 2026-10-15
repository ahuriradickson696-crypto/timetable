"""Admin-only data API — MongoDB. Auth via JWT or X-API-Key."""
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from datetime import datetime

from app.db.mongodb import (
    users_col, programmes_col, cohorts_col, course_units_col,
    lecturers_col, rooms_col, time_periods_col, activities_col,
    enrollments_col, timetable_runs_col, timetable_assignments_col,
    api_keys_col,
)
from app.api.deps import get_current_user_optional

router = APIRouter(prefix="/api/admin/v1", tags=["admin-api"])


async def verify_admin(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    api_key: Optional[str] = None,
    current: Optional[dict] = Depends(get_current_user_optional),
):
    if x_api_key or api_key:
        provided = x_api_key or api_key
        row = await api_keys_col().find_one({"key": provided, "active": True})
        if not row:
            raise HTTPException(401, "Invalid or inactive API key")
        await api_keys_col().update_one(
            {"_id": row["_id"]},
            {"$set": {"last_used_at": datetime.utcnow()}, "$inc": {"call_count": 1}},
        )
        return row
    if current and current.get("role") in ("admin", "officer"):
        return current
    raise HTTPException(403, "Admin access required")


async def _all(coll):
    rows = await coll.find().to_list(5000)
    for r in rows:
        r["_id"] = str(r["_id"])
    return rows


@router.get("/")
async def root():
    return {"name": "AVIU Admin Data API", "version": "1.0.0"}


@router.get("/users")
async def users(_=Depends(verify_admin)):
    rows = await users_col().find().to_list(5000)
    for r in rows:
        r.pop("hashed_password", None)
        r["_id"] = str(r["_id"])
    return rows


@router.get("/students")
async def students(_=Depends(verify_admin)):
    rows = await users_col().find({"role": "student"}).to_list(5000)
    for r in rows:
        r.pop("hashed_password", None)
        r["_id"] = str(r["_id"])
    return rows


@router.get("/employees")
async def employees(_=Depends(verify_admin)):
    rows = await users_col().find({"role": {"$ne": "student"}}).to_list(5000)
    for r in rows:
        r.pop("hashed_password", None)
        r["_id"] = str(r["_id"])
    return rows


@router.get("/programmes")
async def programmes(_=Depends(verify_admin)):
    return await _all(programmes_col())


@router.get("/cohorts")
async def cohorts(_=Depends(verify_admin)):
    return await _all(cohorts_col())


@router.get("/course-units")
async def course_units(_=Depends(verify_admin)):
    return await _all(course_units_col())


@router.get("/lecturers")
async def lecturers(_=Depends(verify_admin)):
    return await _all(lecturers_col())


@router.get("/rooms")
async def rooms(_=Depends(verify_admin)):
    return await _all(rooms_col())


@router.get("/activities")
async def activities(_=Depends(verify_admin)):
    return await _all(activities_col())


@router.get("/enrollments")
async def enrollments(_=Depends(verify_admin)):
    return await _all(enrollments_col())


@router.get("/timetable-runs")
async def runs(_=Depends(verify_admin)):
    return await _all(timetable_runs_col())


@router.get("/dump")
async def dump(_=Depends(verify_admin)):
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "counts": {
            "users": await users_col().count_documents({}),
            "students": await users_col().count_documents({"role": "student"}),
            "lecturers": await lecturers_col().count_documents({}),
            "programmes": await programmes_col().count_documents({}),
            "cohorts": await cohorts_col().count_documents({}),
            "course_units": await course_units_col().count_documents({}),
            "rooms": await rooms_col().count_documents({}),
            "activities": await activities_col().count_documents({}),
            "enrollments": await enrollments_col().count_documents({}),
            "timetable_runs": await timetable_runs_col().count_documents({}),
        },
        "users": await users(dict(_)),
        "programmes": await _all(programmes_col()),
        "cohorts": await _all(cohorts_col()),
        "course_units": await _all(course_units_col()),
        "lecturers": await _all(lecturers_col()),
        "rooms": await _all(rooms_col()),
        "activities": await _all(activities_col()),
        "enrollments": await _all(enrollments_col()),
        "timetable_runs": await _all(timetable_runs_col()),
    }