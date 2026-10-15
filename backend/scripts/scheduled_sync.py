"""One-shot pipeline run for Windows Task Scheduler / cron.

Usage:
    py scripts/scheduled_sync.py

Logs to: logs/scheduled_sync.log
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from app.db.session import SessionLocal
from app.services.pipeline import full_sync
from app.services import upload_manager
from app.core.logging import setup_logging, logger

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "scheduled_sync.log")


def _append_log(text: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] {text}\n")


def main():
    setup_logging()
    _append_log("=== Scheduled sync started ===")

    info = upload_manager.get_current_upload_info()
    if not info:
        msg = "No current file found in uploads/. Skipping."
        logger.warning(msg)
        _append_log(msg)
        return

    logger.info(f"Running pipeline on {info['path']}")
    _append_log(f"File: {info['path']} ({info['size_bytes']} bytes)")

    db = SessionLocal()
    try:
        result = full_sync(
            db,
            workbook_path=info["path"],
            intake="Aug",
            academic_year="2026/2027",
            semester=1,
            import_excel=True,
            auto_generate_activities=True,
            auto_assign_lecturers_flag=True,
            replace_existing=False,
            generate_teaching=True,
            generate_exams=False,
            auto_publish=False,
            created_by=None,
        )
        status = result.get("status", "unknown")
        logger.info(f"Pipeline status: {status}")
        _append_log(f"Status: {status}")

        for step, data in result.get("steps", {}).items():
            line = f"  {step}: {data}"
            logger.info(line)
            _append_log(line)

        for w in result.get("warnings", [])[:5]:
            _append_log(f"  WARN: {w}")
    except Exception as e:
        logger.exception("Scheduled sync failed")
        _append_log(f"FAILED: {e}")
    finally:
        db.close()

    _append_log("=== Scheduled sync finished ===\n")


if __name__ == "__main__":
    main()