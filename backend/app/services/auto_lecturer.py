"""Auto-assign lecturers to activities by qualification + load balance."""
from typing import Dict, List
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.models.activity import Activity
from app.models.lecturer import Lecturer, LecturerModule
from app.models.cohort import Cohort
from app.core.logging import logger


def _lecturers_for_module(db: Session, module_code: str) -> List[Lecturer]:
    """Return lecturers qualified to teach this module."""
    linked_ids = list(db.scalars(
        select(LecturerModule.lecturer_id).where(
            LecturerModule.course_unit_code == module_code
        )
    ))
    if linked_ids:
        return list(db.scalars(select(Lecturer).where(
            Lecturer.id.in_(linked_ids),
            Lecturer.active == True,  # noqa: E712
        )))
    return []


def auto_assign_lecturers(
    db: Session,
    intake: str = "Aug",
    academic_year: str = "2026/2027",
    semester: int = 1,
    replace_placeholders_only: bool = True,
) -> Dict:
    """Assign real lecturers to teaching activities."""
    stats = {"assigned": 0, "unchanged": 0, "no_qualified": 0, "total": 0}
    warnings: List[str] = []

    stmt = select(Activity).where(
        Activity.intake == intake,
        Activity.academic_year == academic_year,
        Activity.semester == semester,
        Activity.activity_type == "teaching",
    )
    if replace_placeholders_only:
        stmt = stmt.where(Activity.lecturer_id == "LECT-001")

    activities = list(db.scalars(stmt))
    stats["total"] = len(activities)

    if not activities:
        return {"status": "ok", "stats": stats, "warnings": ["No activities to assign"]}

    all_lecturers = list(db.scalars(select(Lecturer).where(Lecturer.active == True)))  # noqa: E712
    lect_max = {l.id: l.max_hours_per_week for l in all_lecturers}
    lect_pref = {l.id: l.preferred_mode for l in all_lecturers}

    cohort_modes = {c.id: c.mode for c in db.scalars(select(Cohort))}

    # Current load (excluding LECT-001 placeholders)
    current_load: Dict[str, int] = defaultdict(int)
    for a in db.scalars(select(Activity).where(
        Activity.activity_type == "teaching",
        Activity.lecturer_id != "LECT-001",
    )):
        current_load[a.lecturer_id] += a.duration_periods

    # Sort by duration descending (harder first)
    activities.sort(key=lambda a: -a.duration_periods)

    for act in activities:
        qualified = _lecturers_for_module(db, act.module_code)
        if not qualified:
            stats["no_qualified"] += 1
            warnings.append(f"No qualified lecturer for {act.module_code} ({act.id})")
            continue

        cohort_mode = cohort_modes.get(act.cohort_id, "Day")

        def score(l: Lecturer):
            load = current_load[l.id]
            max_h = lect_max.get(l.id, 16)
            headroom = max_h - load
            mode_penalty = 0 if l.preferred_mode in (cohort_mode, "Both") else 1
            return (mode_penalty, -headroom, load)

        candidates = [l for l in qualified if current_load[l.id] + act.duration_periods <= lect_max.get(l.id, 16)]
        if not candidates:
            candidates = qualified
            warnings.append(f"All qualified lecturers full for {act.module_code}, allowing overflow")

        candidates.sort(key=score)
        chosen = candidates[0]

        old = act.lecturer_id
        act.lecturer_id = chosen.id
        current_load[chosen.id] += act.duration_periods

        if old != chosen.id:
            stats["assigned"] += 1
        else:
            stats["unchanged"] += 1

    db.commit()
    logger.info(f"Auto-assign lecturers: {stats}")
    return {"status": "ok", "stats": stats, "warnings": warnings}