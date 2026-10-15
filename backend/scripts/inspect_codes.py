"""Inspect course unit codes."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.db.session import SessionLocal
from app.models.course_unit import CourseUnit
from app.models.cohort import Cohort

db = SessionLocal()
try:
    print("=" * 70)
    print("COURSE UNIT CODE ANALYSIS")
    print("=" * 70)

    # Sample codes
    print("\nFirst 15 BSE course units:")
    for u in db.query(CourseUnit).filter(CourseUnit.code.like("BSE%")).limit(15).all():
        code = u.code
        last = code.split()[-1] if " " in code else code
        print(f"  {code:30s}  code_part='{last}'  len={len(last)}")

    print("\nFirst 15 DCM course units:")
    for u in db.query(CourseUnit).filter(CourseUnit.code.like("DCM%")).limit(15).all():
        code = u.code
        last = code.split()[-1] if " " in code else code
        print(f"  {code:30s}  code_part='{last}'  len={len(last)}")

    print("\nFirst 5 DMLT course units:")
    for u in db.query(CourseUnit).filter(CourseUnit.code.like("DMLT%")).limit(5).all():
        code = u.code
        last = code.split()[-1] if " " in code else code
        print(f"  {code:30s}  code_part='{last}'  len={len(last)}")

    # Cohort info
    print("\nCohorts:")
    for c in db.query(Cohort).all():
        print(f"  {c.id}  prog={c.programme_code}  year={c.year_level}  sem={c.semester}")

    # Test _units_for_cohort
    print("\n" + "=" * 70)
    print("TESTING _units_for_cohort")
    print("=" * 70)
    from app.services.auto_activity import _units_for_cohort, _extract_year_from_code, _extract_semester_from_code
    for c in db.query(Cohort).all():
        units = _units_for_cohort(db, c, 1)
        print(f"  {c.id}: {len(units)} units match")
        if units[:3]:
            for u in units[:3]:
                print(f"       {u.code}")

    # Test parser
    print("\n" + "=" * 70)
    print("PARSER TESTS")
    print("=" * 70)
    for code in ["BSE ED 71101", "BSE BI 71105", "DCM CS 51101", "DCM AP 51103", "DMLT LB 51104"]:
        y = _extract_year_from_code(code)
        s = _extract_semester_from_code(code)
        print(f"  {code:20s}  year={y}  semester={s}")
finally:
    db.close()