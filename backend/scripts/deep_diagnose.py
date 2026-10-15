"""Deep diagnosis of infeasibility."""
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
    print("DEEP INFEASIBILITY DIAGNOSIS")
    print("=" * 70)

    print(f"\nTotal teaching activities: {len(activities)}")
    print(f"Total Day periods (Mon-Fri): {len(periods)}")

    # By cohort
    print(f"\n── Cohort loads ──")
    by_cohort = defaultdict(list)
    for a in activities:
        by_cohort[a.cohort_id].append(a)
    for cid, acts in sorted(by_cohort.items()):
        hours = sum(a.duration_periods for a in acts)
        joint_count = sum(1 for a in acts if a.joint_cohort_ids)
        print(f"  {cid}: {len(acts)} activities, {hours} hours, {joint_count} joint")

    # By lecturer
    print(f"\n── Lecturer loads ──")
    by_lect = defaultdict(list)
    for a in activities:
        by_lect[a.lecturer_id].append(a)
    over = []
    for lid, acts in sorted(by_lect.items()):
        hours = sum(a.duration_periods for a in acts)
        lect = db.get(Lecturer, lid)
        max_h = lect.max_hours_per_week if lect else 0
        marker = " ⚠ OVER" if hours > max_h else ""
        print(f"  {lid}: {hours}h / {max_h}h{marker}")
        if hours > max_h:
            over.append(lid)

    # By room type
    print(f"\n── Room type demand ──")
    by_rt = defaultdict(list)
    for a in activities:
        by_rt[a.preferred_room_type].append(a)
    for rt, acts in sorted(by_rt.items()):
        hours = sum(a.duration_periods for a in acts)
        rooms = db.query(Room).filter_by(room_type=rt, active=True).all()
        capacity = len(rooms) * len(periods)
        marker = " ⚠ OVER" if hours > capacity else ""
        print(f"  {rt}: {len(acts)} activities, {hours}h; {len(rooms)} rooms × {len(periods)} slots = {capacity} capacity{marker}")
        for r in rooms[:3]:
            print(f"      {r.code}: capacity={r.capacity}")

    # Student sizes vs rooms
    print(f"\n── Student size issues ──")
    for a in activities:
        fitting_rooms = [r for r in db.query(Room).filter_by(room_type=a.preferred_room_type, active=True) if r.capacity >= a.students]
        if not fitting_rooms:
            print(f"  ⚠ {a.id}: {a.students} students, no {a.preferred_room_type} room fits!")

    # Joint activity chains
    print(f"\n── Joint activity chains ──")
    joint = [a for a in activities if a.joint_cohort_ids]
    for a in joint[:5]:
        cohorts_str = f"{a.cohort_id} + {a.joint_cohort_ids}"
        print(f"  {a.id}: needs all of [{cohorts_str}] free simultaneously")

    # Sum of needed hours vs capacity
    print(f"\n── Total capacity check ──")
    total_hours = sum(a.duration_periods for a in activities)
    print(f"  Total hours needed: {total_hours}")
    print(f"  Room-slot capacity: {len(periods)} periods × {db.query(Room).filter_by(active=True).count()} rooms = {len(periods) * db.query(Room).filter_by(active=True).count()}")
    print(f"  Room capacity OK: {total_hours <= len(periods) * db.query(Room).filter_by(active=True).count()}")

    print("=" * 70)
finally:
    db.close()