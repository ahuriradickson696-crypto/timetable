"""Auto-generate activities from curriculum + cohorts."""

from typing import Dict, List
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.cohort import Cohort
from app.models.course_unit import CourseUnit, CourseUnitProgramme
from app.models.activity import Activity
from app.core.logging import logger


MAX_UNITS_PER_COHORT = 8


def _extract_year_from_code(module_code: str):
    tokens = module_code.split()
    if len(tokens) < 3:
        return None
    code_part = tokens[-1]
    if len(code_part) < 4:
        return None
    try:
        return int(code_part[1])
    except (ValueError, IndexError):
        return None


def _extract_semester_from_code(module_code: str):
    tokens = module_code.split()
    if len(tokens) < 3:
        return None
    code_part = tokens[-1]
    if len(code_part) < 4:
        return None
    try:
        return int(code_part[2])
    except (ValueError, IndexError):
        return None


def _is_common_to_multiple_cohorts(unit: CourseUnit) -> bool:
    notes = (unit.notes or "").lower()
    return (
        "common to both" in notes
        or "common to all" in notes
        or "shared" in notes
        or "joint" in notes
    )


def _units_for_cohort(db: Session, cohort: Cohort, semester: int) -> List[CourseUnit]:
    stmt = select(CourseUnit).where(
        CourseUnit.active == True,  # noqa: E712
        CourseUnit.contact_hours_per_week > 0,
    )
    units = list(db.scalars(stmt))

    result = []
    for u in units:
        program_matches = False
        linked = db.scalar(
            select(CourseUnitProgramme).where(
                CourseUnitProgramme.course_unit_code == u.code,
                CourseUnitProgramme.programme_code == cohort.programme_code,
            )
        )
        if linked:
            program_matches = True
        else:
            first_token = u.code.split()[0].upper() if " " in u.code else u.code.upper()
            if first_token == cohort.programme_code.upper():
                program_matches = True
        if not program_matches:
            continue

        u_year = _extract_year_from_code(u.code)
        if u_year is not None and u_year != cohort.year_level:
            continue

        u_sem = _extract_semester_from_code(u.code)
        if u_sem is not None and u_sem != semester:
            continue

        result.append(u)
    return result


def _cohort_slug(cohort_id: str) -> str:
    """Return a UNIQUE short identifier per cohort.

    BSE-BC-Y1-Day-Aug2026 → BC
    BSE-MP-Y1-Day-Aug2026 → MP
    DCM-Y1-Day-Aug2026    → DCM
    DMLT-Y1-Day-Aug2026   → DMLT
    """
    parts = [p for p in cohort_id.split("-") if p]
    # Skip known suffixes
    skip = {"Y1", "Y2", "Y3", "Y4", "Day", "Weekend", "Aug", "Jan", "May"}
    remaining = [p for p in parts if p not in skip]
    # Drop digits-only tails (year numbers etc)
    remaining = [p for p in remaining if not p.isdigit()]
    if not remaining:
        return cohort_id[:6]
    # If there's a short combination marker (BC/MP), use it prefixed by programme
    if len(remaining) >= 2 and len(remaining[1]) <= 3:
        return remaining[0] + remaining[1]
    return "".join(remaining[:2])


def generate_activities_for_semester(
    db: Session,
    intake: str = "Aug",
    academic_year: str = "2026/2027",
    semester: int = 1,
    activity_type: str = "teaching",
    replace_existing: bool = False,
    max_units_per_cohort: int = MAX_UNITS_PER_COHORT,
) -> Dict:
    stats = {"created": 0, "skipped": 0, "cohorts": 0, "units_found": 0, "capped": 0, "joint": 0, "per_cohort": 0}
    warnings: List[str] = []

    cohorts = list(db.scalars(select(Cohort).where(
        Cohort.intake == intake,
        Cohort.academic_year == academic_year,
        Cohort.semester == semester,
        Cohort.status == "Active",
    )))

    if not cohorts:
        return {"error": f"No active cohorts for {intake} {academic_year} Sem {semester}"}

    stats["cohorts"] = len(cohorts)

    if replace_existing:
        from app.models.timetable import TimetableAssignment
        existing = list(db.scalars(select(Activity).where(
            Activity.intake == intake,
            Activity.academic_year == academic_year,
            Activity.semester == semester,
            Activity.activity_type == activity_type,
        )))
        for e in existing:
            for assn in db.query(TimetableAssignment).filter_by(activity_id=e.id):
                db.delete(assn)
            db.delete(e)
        db.commit()

    unit_cohorts: Dict[str, List[Cohort]] = defaultdict(list)

    for cohort in cohorts:
        units = _units_for_cohort(db, cohort, semester)
        units.sort(key=lambda u: (u.is_cross_cutting, u.code))
        if len(units) > max_units_per_cohort:
            stats["capped"] += len(units) - max_units_per_cohort
            units = units[:max_units_per_cohort]
        stats["units_found"] += len(units)
        for u in units:
            unit_cohorts[u.code].append(cohort)

    for unit_code, matched_cohorts in unit_cohorts.items():
        unit = db.get(CourseUnit, unit_code)
        if not unit:
            continue

        make_joint = _is_common_to_multiple_cohorts(unit) and len(matched_cohorts) > 1

        if make_joint:
            primary = matched_cohorts[0]
            joint = ",".join(c.id for c in matched_cohorts[1:])
            # JOINT id uses primary cohort slug + "J"
            slug = _cohort_slug(primary.id)
            safe_code = unit_code.replace(" ", "").replace("/", "")
            aid = f"ACT-{safe_code}-{slug}J"
            if db.get(Activity, aid) and not replace_existing:
                stats["skipped"] += 1
                continue
            total_students = sum(c.estimated_students for c in matched_cohorts)
            duration = min(2, max(1, unit.contact_hours_per_week or 2))
            db.add(Activity(
                id=aid,
                cohort_id=primary.id,
                module_code=unit_code,
                lecturer_id="LECT-001",
                duration_periods=duration,
                preferred_room_type=unit.preferred_room_type or "Lecture",
                students=total_students,
                split_allowed=False,
                joint_cohort_ids=joint,
                semester=semester,
                intake=intake,
                academic_year=academic_year,
                activity_type=activity_type,
                notes=f"JOINT: {', '.join(c.id for c in matched_cohorts)}",
            ))
            stats["created"] += 1
            stats["joint"] += 1
        else:
            for cohort in matched_cohorts:
                slug = _cohort_slug(cohort.id)
                safe_code = unit_code.replace(" ", "").replace("/", "")
                aid = f"ACT-{safe_code}-{slug}"
                if db.get(Activity, aid) and not replace_existing:
                    stats["skipped"] += 1
                    continue
                duration = min(2, max(1, unit.contact_hours_per_week or 2))
                db.add(Activity(
                    id=aid,
                    cohort_id=cohort.id,
                    module_code=unit_code,
                    lecturer_id="LECT-001",
                    duration_periods=duration,
                    preferred_room_type=unit.preferred_room_type or "Lecture",
                    students=cohort.estimated_students,
                    split_allowed=False,
                    joint_cohort_ids=None,
                    semester=semester,
                    intake=intake,
                    academic_year=academic_year,
                    activity_type=activity_type,
                    notes=f"Auto-gen for {cohort.id}",
                ))
                stats["created"] += 1
                stats["per_cohort"] += 1

    db.commit()
    logger.info(f"Auto-activity: {stats}")
    return {"status": "ok", "stats": stats, "warnings": warnings}