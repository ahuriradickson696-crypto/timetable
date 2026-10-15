"""Diagnose why solver is infeasible."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from collections import defaultdict
from app.db.session import SessionLocal
from app.models.activity import Activity
from app.models.lecturer import Lecturer
from app.models.cohort import Cohort
from app.models.room import Room
from app.models.time_period import TimePeriod

db = SessionLocal()
try:
    activities = db.query(Activity).filter_by(activity_type="teaching").all()
    periods = db.query(TimePeriod).filter_by(mode="Day", is_break=False).all()

    print("=" * 70)
    print("INFEASIBILITY DIAGNOSIS")
    print("=" * 70)

    # 1. Available Day periods
    periods_per_day = defaultdict(int)
    for p in periods:
        periods_per_day[p.day] += 1
    print(f"\n1. Day periods available (excluding breaks):")
    for d, c in periods_per_day.items():
        print(f"     {d}: {c} slots")
    print(f"     TOTAL: {len(periods)} slots per week")

    # 2. Cohort load
    print(f"\n2. Hours required per cohort:")
    cohort_load = defaultdict(int)
    cohort_activity_count = defaultdict(int)
    for a in activities:
        cohort_load[a.cohort_id] += a.duration_periods
        cohort_activity_count[a.cohort_id] += 1
    for cid, h in sorted(cohort_load.items()):
        print(f"     {cid}: {cohort_activity_count[cid]} activities, {h} hours")
    total_hours = sum(cohort_load.values())
    print(f"     TOTAL cohort-hours needed: {total_hours}")

    # 3. Lecturer load
    print(f"\n3. Lecturer load:")
    lect_load = defaultdict(int)
    for a in activities:
        lect_load[a.lecturer_id] += a.duration_periods
    for lid, h in sorted(lect_load.items()):
        lect = db.get(Lecturer, lid)
        max_h = lect.max_hours_per_week if lect else 0
        flag = "  <-- OVER MAX" if h > max_h else ""
        print(f"     {lid}: {h}h / max {max_h}h{flag}")

    # 4. Room capacity check
    print(f"\n4. Room constraints:")
    print(f"     Total rooms: {db.query(Room).count()}")
    for a in activities[:3]:
        rooms_fit = [r.code for r in db.query(Room).all() if r.capacity >= a.students and r.active]
        print(f"     {a.id}: {a.students} students, fits in {len(rooms_fit)} rooms")

    # 5. Joint activities
    print(f"\n5. Joint activities (need sync of multiple cohorts):")
    joint = [a for a in activities if a.joint_cohort_ids]
    print(f"     Total joint: {len(joint)} of {len(activities)}")

    # 6. Preferred room types
    print(f"\n6. Activities by preferred room type:")
    room_pref = defaultdict(int)
    for a in activities:
        room_pref[a.preferred_room_type] += 1
    for rt, c in sorted(room_pref.items()):
        matching = db.query(Room).filter_by(room_type=rt, active=True).count()
        print(f"     {rt}: {c} activities, {matching} matching rooms")

    print("=" * 70)
finally:
    db.close()