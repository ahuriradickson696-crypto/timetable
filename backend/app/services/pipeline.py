"""One-click pipeline: import Excel -> auto-generate -> auto-assign -> solve -> publish."""
import os, json
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.services.import_excel import import_from_excel
from app.services.auto_activity import generate_activities_for_semester
from app.services.auto_lecturer import auto_assign_lecturers
from app.services.solver.runner import generate_timetable
from app.models.timetable import TimetableRun
from app.core.logging import logger


DEFAULT_WORKBOOK = r"C:\Users\MAS GLOBAL TECH\aviu-timetable\data\AVIU_Timetable_Master_Data_Workbook.xlsx"


def full_sync(
    db: Session,
    workbook_path: Optional[str] = None,
    intake: str = "Aug",
    academic_year: str = "2026/2027",
    semester: int = 1,
    import_excel: bool = True,
    auto_generate_activities: bool = True,
    auto_assign_lecturers_flag: bool = True,
    replace_existing: bool = False,
    generate_teaching: bool = True,
    generate_exams: bool = False,
    auto_publish: bool = False,
    created_by: Optional[int] = None,
) -> Dict:
    """Run the entire pipeline in one call."""
    result: Dict = {
        "status": "ok",
        "steps": {},
        "warnings": [],
    }

    # ---- Step 1: Import Excel
    if import_excel:
        path = workbook_path or DEFAULT_WORKBOOK
        if not os.path.exists(path):
            result["status"] = "failed"
            result["steps"]["import"] = {"error": f"Workbook not found: {path}"}
            return result
        try:
            logger.info(f"[pipeline] Importing {path}")
            r = import_from_excel(db, path)
            result["steps"]["import"] = {"status": "ok", "stats": r.get("stats", {})}
        except Exception as e:
            logger.exception("Import failed")
            result["status"] = "failed"
            result["steps"]["import"] = {"error": str(e)}
            return result

    # ---- Step 2: Auto-generate activities
    if auto_generate_activities:
        try:
            logger.info("[pipeline] Generating activities from curriculum")
            r = generate_activities_for_semester(
                db, intake=intake, academic_year=academic_year,
                semester=semester, activity_type="teaching",
                replace_existing=replace_existing,
            )
            if "error" in r:
                result["warnings"].append(r["error"])
                result["steps"]["activities"] = {"status": "skip", "message": r["error"]}
            else:
                result["steps"]["activities"] = {"status": "ok", "stats": r.get("stats", {})}
        except Exception as e:
            logger.exception("Activity generation failed")
            result["warnings"].append(f"Activity gen: {e}")
            result["steps"]["activities"] = {"status": "error", "error": str(e)}

    # ---- Step 3: Auto-assign lecturers
    if auto_assign_lecturers_flag:
        try:
            logger.info("[pipeline] Assigning lecturers")
            r = auto_assign_lecturers(
                db, intake=intake, academic_year=academic_year,
                semester=semester, replace_placeholders_only=False,
            )
            result["steps"]["lecturers"] = {"status": "ok", "stats": r.get("stats", {})}
            for w in r.get("warnings", [])[:5]:
                result["warnings"].append(w)
        except Exception as e:
            logger.exception("Lecturer assignment failed")
            result["warnings"].append(f"Lecturer assign: {e}")
            result["steps"]["lecturers"] = {"status": "error", "error": str(e)}

    # ---- Step 4: Generate timetables
    if generate_teaching:
        try:
            logger.info("[pipeline] Running teaching solver")
            run = generate_timetable(
                db, intake=intake, academic_year=academic_year,
                semester=semester, run_type="teaching", created_by=created_by,
            )
            result["steps"]["teaching_run"] = {
                "id": run.id, "status": run.status, "message": run.message,
            }
            if auto_publish and run.status == "success":
                run.is_published = True
                run.is_locked = True
                db.commit()
                result["steps"]["teaching_run"]["published"] = True
        except Exception as e:
            logger.exception("Teaching solve failed")
            result["warnings"].append(f"Teaching solve: {e}")
            result["steps"]["teaching_run"] = {"status": "error", "error": str(e)}

    if generate_exams:
        try:
            logger.info("[pipeline] Running exam solver")
            run = generate_timetable(
                db, intake=intake, academic_year=academic_year,
                semester=semester, run_type="exam", created_by=created_by,
            )
            result["steps"]["exam_run"] = {
                "id": run.id, "status": run.status, "message": run.message,
            }
            if auto_publish and run.status == "success":
                run.is_published = True
                run.is_locked = True
                db.commit()
                result["steps"]["exam_run"]["published"] = True
        except Exception as e:
            logger.exception("Exam solve failed")
            result["warnings"].append(f"Exam solve: {e}")
            result["steps"]["exam_run"] = {"status": "error", "error": str(e)}

    logger.info(f"[pipeline] Complete: {result['status']}")
    return result