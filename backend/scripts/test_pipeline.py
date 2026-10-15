"""Test the full pipeline from scratch."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.db.session import SessionLocal
from app.services.pipeline import full_sync

db = SessionLocal()
try:
    print("=" * 60)
    print("RUNNING FULL PIPELINE")
    print("=" * 60)
    result = full_sync(
        db,
        intake="Aug",
        academic_year="2026/2027",
        semester=1,
        import_excel=False,        # workbook already imported
        auto_generate_activities=True,
        auto_assign_lecturers_flag=True,
        replace_existing=False,
        generate_teaching=True,
        generate_exams=False,
        auto_publish=False,
    )
    print()
    print(f"STATUS: {result['status']}")
    print()
    for step, data in result["steps"].items():
        print(f"  [{step}]  {data}")
    if result["warnings"]:
        print()
        print("Warnings:")
        for w in result["warnings"]:
            print(f"  - {w}")
    print("=" * 60)
finally:
    db.close()