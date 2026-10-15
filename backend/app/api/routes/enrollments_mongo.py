"""Enrollments — MongoDB."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from bson import ObjectId

from app.db.mongodb import enrollments_col, users_col, course_units_col
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/enrollments", tags=["enrollments"])


class EnrollRequest(BaseModel):
    module_code: str
    academic_year: str = "2026/2027"
    semester: int = 1
    cohort_id: Optional[str] = None


@router.get("/me")
async def my_enrollments(current=Depends(get_current_user)):
    if current.get("role") != "student":
        raise HTTPException(400, "Only students can use this endpoint")
    rows = await enrollments_col().find({"student_id": current["_id"]}).to_list(500)
    for r in rows:
        r["_id"] = str(r["_id"])
    return rows


@router.post("/me", status_code=201)
async def enroll_self(body: EnrollRequest, current=Depends(get_current_user)):
    if current.get("role") != "student":
        raise HTTPException(400, "Only students can use this endpoint")

    cu = await course_units_col().find_one({"code": body.module_code})
    if not cu:
        raise HTTPException(404, "Module not found")

    # Attach cohort if provided and user has none
    if body.cohort_id and not current.get("cohort_id"):
        await users_col().update_one(
            {"_id": ObjectId(current["_id"])},
            {"$set": {"cohort_id": body.cohort_id}},
        )

    existing = await enrollments_col().find_one({
        "student_id": current["_id"],
        "module_code": body.module_code,
        "academic_year": body.academic_year,
        "semester": body.semester,
        "status": "enrolled",
    })
    if existing:
        raise HTTPException(400, "Already enrolled")

    doc = {
        "student_id": current["_id"],
        "module_code": body.module_code,
        "academic_year": body.academic_year,
        "semester": body.semester,
        "status": "enrolled",
        "cohort_id": body.cohort_id or current.get("cohort_id"),
        "enrolled_at": datetime.utcnow(),
    }
    result = await enrollments_col().insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc