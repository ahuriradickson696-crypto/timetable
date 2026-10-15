"""Automation endpoints: file upload + full pipeline."""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.api.deps import get_current_user, require_officer
from app.models.user import User
from app.services import upload_manager
from app.services.pipeline import full_sync, DEFAULT_WORKBOOK
from app.core.logging import logger


router = APIRouter(prefix="/automation", tags=["automation"])


@router.get("/status")
def status(_: User = Depends(get_current_user)):
    """Current upload status."""
    return {
        "current": upload_manager.get_current_upload_info(),
        "default_workbook": DEFAULT_WORKBOOK,
    }


@router.post("/preview")
async def preview(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    """Upload a file and get a diff WITHOUT applying it."""
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(400, "Only .xlsx files allowed")
    contents = await file.read()
    try:
        meta = upload_manager.save_upload(contents, file.filename)
    except ValueError as e:
        raise HTTPException(400, str(e))

    diff = upload_manager.diff_against_db(db, meta["saved_path"])
    return {
        "meta": meta,
        "diff": diff,
    }


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    auto_publish: bool = False,
    run_solver: bool = True,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    """Upload Excel and run the FULL pipeline automatically."""
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(400, "Only .xlsx files allowed")

    contents = await file.read()
    try:
        meta = upload_manager.save_upload(contents, file.filename)
    except ValueError as e:
        raise HTTPException(400, str(e))

    logger.info(f"[upload] Saved {file.filename} ({meta['size_bytes']} bytes)")

    # Run the full pipeline
    try:
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
            generate_teaching=run_solver,
            generate_exams=False,
            auto_publish=auto_publish,
            created_by=current.id,
        )
    except Exception as e:
        logger.exception("Pipeline failed")
        raise HTTPException(500, f"Pipeline failed: {e}")

    return {
        "meta": meta,
        "pipeline": result,
    }


@router.post("/trigger")
def trigger(
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    """Manually trigger the full pipeline using the current saved file."""
    info = upload_manager.get_current_upload_info()
    if not info:
        raise HTTPException(400, "No uploaded file found. Please upload an Excel file first.")

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
        created_by=current.id,
    )
    return result


@router.get("/archives")
def archives(_: User = Depends(get_current_user)):
    """List previous uploads."""
    return upload_manager.list_archives()


@router.post("/rollback/{archive_name}")
def rollback(
    archive_name: str,
    _: User = Depends(require_officer),
):
    """Restore an archive as the current file (does not re-run pipeline)."""
    try:
        return upload_manager.rollback_to(archive_name)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))