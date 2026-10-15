"""Check what programmes + modules we actually have."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.programme import Programme
from app.models.course_unit import CourseUnit

db = SessionLocal()
try:
    progs = list(db.scalars(select(Programme).order_by(Programme.code)))
    print("=" * 70)
    print(f"PROGRAMMES: {len(progs)}")
    print("=" * 70)
    for p in progs:
        print(f"  {p.code:8s}  {p.level:12s}  {p.name}")

    units = list(db.scalars(select(CourseUnit)))
    print()
    print("=" * 70)
    print(f"COURSE UNITS: {len(units)}")
    print("=" * 70)

    # Group by programme prefix
    by_prog = {}
    for u in units:
        prefix = u.code.split()[0]
        by_prog.setdefault(prefix, []).append(u)

    for prefix, us in sorted(by_prog.items()):
        print(f"  {prefix:8s}  {len(us)} units")

    print()
    print("Modules per year/semester (sample):")
    for u in units[:5]:
        print(f"  {u.code}  (year={u.normal_year})")
finally:
    db.close()