"""Cohort module lookup - auto-loads units for the wizard."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Optional

from app.db.session import get_db
from app.models.cohort import Cohort
from app.models.course_unit import CourseUnit
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/v1/cohorts", tags=["cohorts"])

@router.get("")
def list_cohorts(db: Session = Depends(get_db)):
    """List all cohorts."""
    from app.models.cohort import Cohort
    rows = db.query(Cohort).order_by(Cohort.id).all()
    return [
        {
            "id": c.id,
            "programme_code": c.programme_code,
            "year_level": c.year_level,
            "mode": c.mode,
            "intake": c.intake,
            "academic_year": c.academic_year,
            "semester": c.semester,
            "estimated_students": c.estimated_students,
            "status": c.status,
        }
        for c in rows
    ]



def build_cohort_id(programme_code, year, mode, intake, academic_year, combination=None):
    ay_start = academic_year.split("/")[0]
    combo = combination + "-" if combination else ""
    return "{}-{}Y{}-{}-{}{}".format(programme_code, combo, year, mode, intake, ay_start)


@router.get("/{cohort_id}/modules")
def get_cohort_modules(cohort_id, db=Depends(get_db), current_user=Depends(get_current_user)):
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404, detail="Cohort not found")

    prefix = "{} %".format(cohort.programme_code)
    units = (
        db.query(CourseUnit)
        .filter(
            CourseUnit.code.like(prefix),
            CourseUnit.normal_year == cohort.year_level,
            CourseUnit.active == True,
        )
        .order_by(CourseUnit.code)
        .all()
    )

    if cohort.programme_code == "BSE":
        if "-BC-" in cohort.id:
            units = [u for u in units if "BC" in (u.notes or "") or u.is_cross_cutting]
        elif "-MP-" in cohort.id:
            units = [u for u in units if "MP" in (u.notes or "") or u.is_cross_cutting]

    if not units:
        raise HTTPException(status_code=404, detail="No modules found")

    return [
        {
            "code": u.code,
            "name": u.name,
            "credit_units": u.credit_units,
            "contact_hours_per_week": u.contact_hours_per_week,
            "preferred_room_type": u.preferred_room_type,
            "is_cross_cutting": u.is_cross_cutting,
        }
        for u in units
    ]


@router.get("/preview")
def preview_cohort(
    programme: str,
    year: int,
    semester: int,
    intake: str,
    academic_year: str,
    mode: str,
    combination: Optional[str] = None,
    db=Depends(get_db),
    current_user=Depends(get_current_user),
):
    cohort_id = build_cohort_id(programme, year, mode, intake, academic_year, combination)
    cohort = db.query(Cohort).filter(Cohort.id == cohort_id).first()
    if not cohort:
        raise HTTPException(status_code=404, detail="No cohort: " + cohort_id)

    modules = get_cohort_modules(cohort_id, db, current_user)
    return {
        "cohort_id": cohort_id,
        "programme": programme,
        "year": year,
        "semester": semester,
        "mode": mode,
        "intake": intake,
        "academic_year": academic_year,
        "total_credit_units": sum(m["credit_units"] for m in modules),
        "modules": modules,
    }