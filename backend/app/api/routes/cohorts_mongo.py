"""Cohorts — MongoDB."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.db.mongodb import cohorts_col, course_units_col
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/cohorts", tags=["cohorts"])


class CohortCreate(BaseModel):
    id: str
    programme_code: str
    year_level: int
    mode: str
    intake: str
    academic_year: str
    semester: int
    estimated_students: int = 30
    status: str = "Active"


@router.get("")
async def list_cohorts(current=Depends(get_current_user)):
    rows = await cohorts_col().find().sort("id", 1).to_list(500)
    for r in rows:
        r["_id"] = str(r["_id"])
    return rows


@router.get("/preview")
async def cohort_preview(
    programme: str,
    year: int,
    semester: int,
    intake: str,
    academic_year: str,
    mode: str,
    combination: Optional[str] = None,
    current=Depends(get_current_user),
):
    ay_start = academic_year.split("/")[0]
    combo = (combination + "-") if combination else ""
    cohort_id = f"{programme}-{combo}Y{year}-{mode}-{intake}{ay_start}"

    cohort = await cohorts_col().find_one({"id": cohort_id})
    if not cohort:
        raise HTTPException(404, f"No cohort: {cohort_id}")

    prefix = programme + " "
    units = await course_units_col().find({
        "code": {"$regex": "^" + prefix},
        "normal_year": year,
        "active": True,
    }).sort("code", 1).to_list(500)

    if programme == "BSE":
        if combination == "BC":
            units = [u for u in units if "BC" in (u.get("notes") or "") or u.get("is_cross_cutting") or (" BI " in u["code"] or " CH " in u["code"])]
        elif combination == "MP":
            units = [u for u in units if "MP" in (u.get("notes") or "") or u.get("is_cross_cutting") or (" MT " in u["code"] or " PY " in u["code"])]

    modules = []
    total = 0
    for u in units:
        modules.append({
            "code": u["code"],
            "name": u["name"],
            "credit_units": u.get("credit_units", 0),
            "contact_hours_per_week": u.get("contact_hours_per_week", 0),
            "preferred_room_type": u.get("preferred_room_type", "Lecture"),
            "is_cross_cutting": u.get("is_cross_cutting", False),
        })
        total += u.get("credit_units", 0)

    return {
        "cohort_id": cohort_id,
        "programme": programme,
        "year": year,
        "semester": semester,
        "mode": mode,
        "intake": intake,
        "academic_year": academic_year,
        "total_credit_units": total,
        "modules": modules,
    }