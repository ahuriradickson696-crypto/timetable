"""Folder watcher: auto-detect new Excel files in data/ and run the pipeline."""
import os
import time
import threading
from datetime import datetime
from typing import Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from app.db.session import SessionLocal
from app.services.pipeline import full_sync
from app.services import upload_manager
from app.core.logging import logger


WATCH_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "data"
))
STABILITY_DELAY = 3       # wait N seconds after last change before triggering
COOLDOWN_SECONDS = 30     # minimum gap between pipeline runs


class ExcelWatcher(FileSystemEventHandler):
    """Watches for .xlsx files being added/changed in the data folder."""

    def __init__(self):
        self._last_run = 0.0
        self._pending_timer: Optional[threading.Timer] = None
        self._lock = threading.Lock()
        self._file_mtimes = {}

    def _is_relevant(self, path: str) -> bool:
        if not path.lower().endswith(".xlsx"):
            return False
        # Ignore files in uploads/archive
        norm = os.path.normpath(path).lower()
        if "uploads" in norm:
            return False
        if "~$" in os.path.basename(path):
            return False
        return True

    def _file_stable(self, path: str) -> bool:
        """Return True if the file hasn't changed in the last STABILITY_DELAY seconds."""
        try:
            mtime = os.path.getmtime(path)
            prev = self._file_mtimes.get(path)
            self._file_mtimes[path] = mtime
            if prev is not None and mtime != prev:
                return False
            time.sleep(0.5)
            mtime2 = os.path.getmtime(path)
            return mtime == mtime2
        except OSError:
            return False

    def _schedule_run(self, path: str):
        with self._lock:
            if self._pending_timer:
                self._pending_timer.cancel()
            self._pending_timer = threading.Timer(
                STABILITY_DELAY, self._run_pipeline, args=(path,)
            )
            self._pending_timer.daemon = True
            self._pending_timer.start()

    def _run_pipeline(self, path: str):
        now = time.time()
        if now - self._last_run < COOLDOWN_SECONDS:
            logger.info(f"[watcher] Cooldown active, skipping {path}")
            return
        if not os.path.exists(path):
            return
        if not self._file_stable(path):
            logger.info(f"[watcher] File still unstable, rescheduling {path}")
            self._schedule_run(path)
            return

        self._last_run = now
        logger.info(f"[watcher] Pipeline triggered by {path}")

        db = SessionLocal()
        try:
            # Copy into uploads/current.xlsx for consistency with upload flow
            with open(path, "rb") as f:
                contents = f.read()
            meta = upload_manager.save_upload(contents, os.path.basename(path))
            logger.info(f"[watcher] Saved as current.xlsx ({meta['size_bytes']} bytes)")

            result = full_sync(
                db,
                workbook_path=meta["saved_path"],
                intake="Aug",
                academic_year="2026/2027",
                semester=1,
                import_excel=True,
                auto_generate_activities=True,
                auto_assign_lecturers_flag=True,
                replace_existing=False,
                generate_teaching=True,
                generate_exams=False,
                auto_publish=True,   # watcher = trust the pipeline
                created_by=None,
            )
            logger.info(f"[watcher] Pipeline result: {result['status']}")
            for step, data in result["steps"].items():
                logger.info(f"[watcher]   {step}: {data}")
        except Exception as e:
            logger.exception(f"[watcher] Pipeline failed: {e}")
        finally:
            db.close()

    def on_created(self, event):
        if not event.is_directory and self._is_relevant(event.src_path):
            logger.info(f"[watcher] Detected new file: {event.src_path}")
            self._schedule_run(event.src_path)

    def on_modified(self, event):
        if not event.is_directory and self._is_relevant(event.src_path):
            logger.info(f"[watcher] Detected modified file: {event.src_path}")
            self._schedule_run(event.src_path)

    def on_moved(self, event):
        if not event.is_directory and self._is_relevant(event.dest_path):
            logger.info(f"[watcher] Detected moved file: {event.dest_path}")
            self._schedule_run(event.dest_path)


def start_watcher():
    """Start the folder watcher (blocking). Call from scripts/watch.py."""
    os.makedirs(WATCH_DIR, exist_ok=True)
    logger.info(f"[watcher] Watching directory: {WATCH_DIR}")
    logger.info(f"[watcher] Stability delay: {STABILITY_DELAY}s, Cooldown: {COOLDOWN_SECONDS}s")

    handler = ExcelWatcher()
    observer = Observer()
    observer.schedule(handler, WATCH_DIR, recursive=False)
    observer.start()

    print(f"👀 Watching {WATCH_DIR}")
    print("   Drop .xlsx files there to trigger the pipeline.")
    print("   Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n👋 Watcher stopped")
    observer.join()