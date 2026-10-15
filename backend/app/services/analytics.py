"""Analytics and reporting services."""
from typing import Dict, List, Any
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.timetable import TimetableRun, TimetableAssignment
from app.models.activity import Activity
from app.models.time_period import TimePeriod
from app.models.room import Room
from app.models.lecturer import Lecturer
from app.models.cohort import Cohort
from app.models.course_unit import CourseUnit


DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _load_run_data(db: Session, run_id: int):
    """Load all assignments for a run, joined with activity + period."""
    rows = db.execute(
        select(TimetableAssignment, Activity, TimePeriod)
        .join(Activity, TimetableAssignment.activity_id == Activity.id)
        .join(TimePeriod, TimetableAssignment.period_id == TimePeriod.id)
        .where(TimetableAssignment.run_id == run_id)
    ).all()
    return rows


# ============================================================
# Room utilisation heatmap
# ============================================================
def room_utilisation(db: Session, run_id: int) -> Dict[str, Any]:
    """Return a heatmap: room × day -> count of classes."""
    rows = _load_run_data(db, run_id)

    # Count classes per room per day
    grid: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    rooms_set = set()
    days_set = set()

    for assn, act, per in rows:
        grid[assn.room_code][per.day] += 1
        rooms_set.add(assn.room_code)
        days_set.add(per.day)

    rooms = sorted(rooms_set)
    days = [d for d in DAY_ORDER if d in days_set]

    # Capacity info
    room_caps = {}
    for r in db.scalars(select(Room)):
        room_caps[r.code] = {"name": r.name, "capacity": r.capacity, "type": r.room_type}

    # Build matrix
    matrix = []
    for room in rooms:
        row = {"room": room, "room_name": room_caps.get(room, {}).get("name", room), "days": []}
        for day in days:
            row["days"].append(grid[room].get(day, 0))
        row["total"] = sum(row["days"])
        matrix.append(row)

    # Max value for color scaling
    max_val = max((max(r["days"]) for r in matrix), default=0)

    return {
        "days": days,
        "rooms": matrix,
        "max_value": max_val,
    }


# ============================================================
# Lecturer load report
# ============================================================
def lecturer_load(db: Session, run_id: int) -> Dict[str, Any]:
    """Return teaching hours per lecturer, sorted by load."""
    rows = _load_run_data(db, run_id)

    load: Dict[str, int] = defaultdict(int)
    for assn, act, per in rows:
        load[act.lecturer_id] += 1  # 1 period per assignment (per week)

    lecturers_info = {}
    for l in db.scalars(select(Lecturer)):
        lecturers_info[l.id] = {
            "name": l.full_name,
            "max_hours": l.max_hours_per_week,
            "preferred_mode": l.preferred_mode,
        }

    items = []
    for lid, hours in load.items():
        info = lecturers_info.get(lid, {})
        max_h = info.get("max_hours", 0) or 1
        items.append({
            "lecturer_id": lid,
            "name": info.get("name", lid),
            "hours": hours,
            "max_hours": info.get("max_hours", 0),
            "utilization_pct": round((hours / max_h) * 100, 1),
            "status": "overloaded" if hours > max_h else ("full" if hours == max_h else "ok"),
        })
    items.sort(key=lambda x: -x["hours"])

    return {"lecturers": items, "total_lecturers": len(items)}


# ============================================================
# Programme summary
# ============================================================
def programme_summary(db: Session, run_id: int) -> Dict[str, Any]:
    """Return activity/hours count per programme."""
    rows = _load_run_data(db, run_id)

    # Cohort -> programme
    cohorts = {c.id: c.programme_code for c in db.scalars(select(Cohort))}

    # Programme -> stats
    stats = defaultdict(lambda: {"activities": 0, "lecturers": set(), "cohorts": set()})

    for assn, act, per in rows:
        prog = cohorts.get(act.cohort_id, "Unknown")
        stats[prog]["activities"] += 1
        stats[prog]["lecturers"].add(act.lecturer_id)
        stats[prog]["cohorts"].add(act.cohort_id)

    result = []
    for prog, s in sorted(stats.items()):
        result.append({
            "programme": prog,
            "activities": s["activities"],
            "unique_lecturers": len(s["lecturers"]),
            "unique_cohorts": len(s["cohorts"]),
        })
    return {"programmes": result}


# ============================================================
# Cohort weekly load
# ============================================================
def cohort_load(db: Session, run_id: int) -> Dict[str, Any]:
    """Return hours per cohort per day."""
    rows = _load_run_data(db, run_id)

    grid: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    cohorts_set = set()
    days_set = set()

    for assn, act, per in rows:
        grid[act.cohort_id][per.day] += 1
        cohorts_set.add(act.cohort_id)
        days_set.add(per.day)

    cohorts = sorted(cohorts_set)
    days = [d for d in DAY_ORDER if d in days_set]

    matrix = []
    for c in cohorts:
        row = {"cohort": c, "days": [], "total": 0}
        for day in days:
            v = grid[c].get(day, 0)
            row["days"].append(v)
            row["total"] += v
        matrix.append(row)

    max_val = max((max(r["days"]) for r in matrix), default=0)
    return {"days": days, "cohorts": matrix, "max_value": max_val}


# ============================================================
# Free slot finder
# ============================================================
def free_slots(
    db: Session,
    run_id: int,
    room_code: str | None = None,
    day: str | None = None,
) -> Dict[str, Any]:
    """Return all free (day, period) slots for a room or across all rooms."""
    rows = _load_run_data(db, run_id)

    # Period grid for the run type
    run = db.get(TimetableRun, run_id)
    mode_map = {"teaching": "Day", "test": "Test", "exam": "Exam"}
    grid_mode = mode_map.get(run.run_type, "Day")
    periods = list(db.scalars(
        select(TimePeriod).where(TimePeriod.mode == grid_mode, TimePeriod.is_break == False)  # noqa: E712
    ))

    occupied = set()
    for assn, act, per in rows:
        occupied.add((assn.room_code, per.day, per.id))

    rooms = [room_code] if room_code else [r.code for r in db.scalars(select(Room))]
    days_filter = [day] if day else DAY_ORDER

    slots = []
    for r in rooms:
        for p in periods:
            if p.day not in days_filter:
                continue
            if (r, p.day, p.id) not in occupied:
                slots.append({
                    "room": r,
                    "day": p.day,
                    "start_time": p.start_time,
                    "end_time": p.end_time,
                    "period_id": p.id,
                })
    slots.sort(key=lambda x: (x["room"], DAY_ORDER.index(x["day"]) if x["day"] in DAY_ORDER else 99, x["start_time"]))

    return {"free_slots": slots, "total": len(slots)}