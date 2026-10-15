"""One-shot script: import the AVIU Master Data Workbook into the database."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.db.session import SessionLocal, engine
from app.db.base import Base
import app.models  # noqa: F401
from app.services.import_excel import import_from_excel

WORKBOOK = r"C:\Users\MAS GLOBAL TECH\aviu-timetable\data\AVIU_Timetable_Master_Data_Workbook.xlsx"


def main():
    print(f"Looking for workbook at: {WORKBOOK}")
    if not os.path.exists(WORKBOOK):
        print("ERROR: Workbook not found.")
        sys.exit(1)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        result = import_from_excel(db, WORKBOOK)
        print()
        print("=" * 60)
        print("IMPORT COMPLETE")
        print("=" * 60)
        for table, s in result["stats"].items():
            ins = s["inserted"]
            upd = s["updated"]
            print(f"  {table:15s} inserted={ins:3d}  updated={upd:3d}")
        if result["warnings"]:
            print()
            print("Warnings:")
            for w in result["warnings"][:15]:
                print(f"  - {w}")
        print("=" * 60)
    finally:
        db.close()


if __name__ == "__main__":
    main()
