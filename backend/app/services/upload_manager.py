"""Handle Excel uploads: save, validate, archive, diff."""
import os
import shutil
import hashlib
import json
from datetime import datetime
from typing import Dict, Optional, List, Any
from openpyxl import load_workbook
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.programme import Programme
from app.models.cohort import Cohort
from app.models.course_unit import CourseUnit
from app.models.lecturer import Lecturer
from app.models.room import Room
from app.models.time_period import TimePeriod
from app.models.activity import Activity
from app.core.logging import logger


UPLOAD_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data", "uploads"
))
ARCHIVE_DIR = os.path.join(UPLOAD_DIR, "archive")
CURRENT_FILE = os.path.join(UPLOAD_DIR, "current.xlsx")
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


def _hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def save_upload(file_bytes: bytes, original_filename: str) -> Dict[str, Any]:
    """Save uploaded file, validate, archive previous, return metadata."""
    if len(file_bytes) > MAX_FILE_SIZE:
        raise ValueError(f"File too large (max {MAX_FILE_SIZE // (1024*1024)} MB)")

    if not original_filename.lower().endswith(".xlsx"):
        raise ValueError("Only .xlsx files allowed")

    os.makedirs(ARCHIVE_DIR, exist_ok=True)

    # Archive current if exists
    archived_path = None
    if os.path.exists(CURRENT_FILE):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        archived_path = os.path.join(ARCHIVE_DIR, f"timetable_{ts}.xlsx")
        shutil.copy2(CURRENT_FILE, archived_path)
        logger.info(f"Archived previous upload to {archived_path}")

    # Save new file
    with open(CURRENT_FILE, "wb") as f:
        f.write(file_bytes)

    # Validate it's a real Excel file
    try:
        wb = load_workbook(CURRENT_FILE, read_only=True)
        sheets = wb.sheetnames
        wb.close()
    except Exception as e:
        os.remove(CURRENT_FILE)
        raise ValueError(f"Invalid Excel file: {e}")

    file_hash = _hash_file(CURRENT_FILE)
    file_size = os.path.getsize(CURRENT_FILE)

    return {
        "filename": original_filename,
        "saved_path": CURRENT_FILE,
        "archived_path": archived_path,
        "hash": file_hash,
        "size_bytes": file_size,
        "sheets": sheets,
        "uploaded_at": datetime.utcnow().isoformat(),
    }


def get_current_upload_info() -> Optional[Dict[str, Any]]:
    """Return info about the currently saved file."""
    if not os.path.exists(CURRENT_FILE):
        return None
    stat = os.stat(CURRENT_FILE)
    try:
        wb = load_workbook(CURRENT_FILE, read_only=True)
        sheets = wb.sheetnames
        wb.close()
    except Exception:
        sheets = []
    return {
        "path": CURRENT_FILE,
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "hash": _hash_file(CURRENT_FILE),
        "sheets": sheets,
    }


def diff_against_db(db: Session, workbook_path: str) -> Dict[str, Any]:
    """Compare Excel contents to current DB — returns what will change."""
    wb = load_workbook(workbook_path, data_only=True)
    result = {
        "programmes": {"new": [], "changed": [], "removed": []},
        "cohorts": {"new": [], "changed": [], "removed": []},
        "course_units": {"new": [], "changed": [], "removed": []},
        "lecturers": {"new": [], "changed": [], "removed": []},
        "rooms": {"new": [], "changed": [], "removed": []},
    }

    def read_sheet_rows(sheet_name: str, marker: str) -> List[Dict[str, Any]]:
        if sheet_name not in wb.sheetnames:
            return []
        ws = wb[sheet_name]
        hdr_row = None
        for i, row in enumerate(ws.iter_rows(min_row=1, max_row=15, values_only=True), 1):
            for cell in row:
                if cell is None:
                    continue
                if str(cell).strip().lower() == marker.lower():
                    hdr_row = i
                    break
                break
            if hdr_row:
                break
        if not hdr_row:
            return []
        header = [str(c).strip() if c else "" for c in next(ws.iter_rows(min_row=hdr_row, max_row=hdr_row, values_only=True))]
        rows = []
        for row in ws.iter_rows(min_row=hdr_row + 1, values_only=True):
            if not any(row):
                continue
            d = dict(zip(header, row))
            if d.get(header[0]):
                rows.append(d)
        return rows

    # Programmes diff
    excel_progs = {r.get("Programme_Code") for r in read_sheet_rows("01_Programmes", "Programme_Code") if r.get("Programme_Code")}
    db_progs = {p.code for p in db.scalars(select(Programme))}
    result["programmes"]["new"] = sorted(excel_progs - db_progs)
    result["programmes"]["removed"] = sorted(db_progs - excel_progs)

    # Cohorts diff
    excel_cohorts = {r.get("Cohort_ID") for r in read_sheet_rows("02_Cohorts", "Cohort_ID") if r.get("Cohort_ID")}
    db_cohorts = {c.id for c in db.scalars(select(Cohort))}
    result["cohorts"]["new"] = sorted(excel_cohorts - db_cohorts)
    result["cohorts"]["removed"] = sorted(db_cohorts - excel_cohorts)

    # Course units diff
    excel_units = {r.get("Module_Code") for r in read_sheet_rows("03_Course_Units", "Module_Code") if r.get("Module_Code")}
    db_units = {u.code for u in db.scalars(select(CourseUnit))}
    result["course_units"]["new"] = sorted(list(excel_units - db_units))[:30]
    result["course_units"]["removed"] = sorted(list(db_units - excel_units))[:30]
    result["course_units"]["new_count"] = len(excel_units - db_units)
    result["course_units"]["removed_count"] = len(db_units - excel_units)

    # Lecturers diff
    excel_lect = {r.get("Lecturer_ID") for r in read_sheet_rows("04_Lecturers", "Lecturer_ID") if r.get("Lecturer_ID")}
    db_lect = {l.id for l in db.scalars(select(Lecturer))}
    result["lecturers"]["new"] = sorted(excel_lect - db_lect)
    result["lecturers"]["removed"] = sorted(db_lect - excel_lect)

    # Rooms diff
    excel_rooms = {r.get("Room_Code") for r in read_sheet_rows("05_Rooms", "Room_Code") if r.get("Room_Code")}
    db_rooms = {r.code for r in db.scalars(select(Room))}
    result["rooms"]["new"] = sorted(excel_rooms - db_rooms)
    result["rooms"]["removed"] = sorted(db_rooms - excel_rooms)

    wb.close()

    # Summary counts
    total_new = sum(len(v["new"]) if isinstance(v["new"], list) else 0 for v in result.values())
    total_removed = sum(len(v["removed"]) if isinstance(v["removed"], list) else 0 for v in result.values())

    return {
        "diff": result,
        "summary": {
            "total_new": total_new,
            "total_removed": total_removed,
            "has_changes": total_new > 0 or total_removed > 0,
        }
    }


def list_archives() -> List[Dict[str, Any]]:
    """List all archived uploads."""
    if not os.path.exists(ARCHIVE_DIR):
        return []
    items = []
    for name in sorted(os.listdir(ARCHIVE_DIR), reverse=True):
        if not name.endswith(".xlsx"):
            continue
        path = os.path.join(ARCHIVE_DIR, name)
        stat = os.stat(path)
        items.append({
            "name": name,
            "path": path,
            "size_bytes": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })
    return items


def rollback_to(archive_name: str) -> Dict[str, Any]:
    """Restore a previous upload as the current file."""
    src = os.path.join(ARCHIVE_DIR, archive_name)
    if not os.path.exists(src):
        raise FileNotFoundError(f"Archive not found: {archive_name}")
    if os.path.exists(CURRENT_FILE):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(CURRENT_FILE, os.path.join(ARCHIVE_DIR, f"pre_rollback_{ts}.xlsx"))
    shutil.copy2(src, CURRENT_FILE)
    return {"restored": archive_name, "path": CURRENT_FILE}