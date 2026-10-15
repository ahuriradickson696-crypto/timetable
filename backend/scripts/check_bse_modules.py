"""Verify modules exist for BSE Year 1 Sem 1."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.course_unit import CourseUnit
from app.services.auto_activity import _extract_year_from_code, _extract_semester_from_code

db = SessionLocal()
try:
    units = list(db.scalars(select(CourseUnit).order_by(CourseUnit.code)))

    print("=" * 70)
    print("BSE MODULES BY YEAR/SEMESTER")
    print("=" * 70)

    grid = {}
    for u in units:
        if not u.code.startswith("BSE"):
            continue
        y = _extract_year_from_code(u.code)
        s = _extract_semester_from_code(u.code)
        if y and s:
            grid.setdefault((y, s), []).append(u)

    for y in [1, 2, 3]:
        for s in [1, 2]:
            count = len(grid.get((y, s), []))
            print(f"  Year {y} Sem {s}: {count} modules")

    print()
    print("=" * 70)
    print("BSE Year 1 Sem 1 modules (should be 12):")
    print("=" * 70)
    for u in grid.get((1, 1), []):
        print(f"  {u.code:25s}  {u.name}")
finally:
    db.close()