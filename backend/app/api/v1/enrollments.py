"""Enrollment endpoints -- student self-service + admin management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.api.deps import get_current_user, require_officer, require_admin
from app.models.user import User, UserRole
from app.models.enrollment import Enrollment
from app.models.course_unit import CourseUnit, CourseUnitProgramme
from app.models.cohort import Cohort
from app.services.changelog import log_change
from app.schemas.enrollment import (
    EnrollmentCreate, AdminEnrollmentCreate, EnrollmentOut,
    BulkAutoEnrollRequest,
)
from app.schemas.common import Message


router = APIRouter(prefix="/enrollments", tags=["enrollments"])


def _enrich(db: Session, e: Enrollment) -> dict:
    cu = db.get(CourseUnit, e.module_code)
    return {
        "id": e.id,
        "student_id": e.student_id,
        "module_code": e.module_code,
        "academic_year": e.academic_year,
        "semester": e.semester,
        "status": e.status,
        "grade": e.grade,
        "enrolled_at": e.enrolled_at,
        "dropped_at": e.dropped_at,
        "completed_at": e.completed_at,
        "is_locked": e.is_locked,
        "notes": e.notes,
        "module_name": cu.name if cu else None,
        "credit_units": cu.credit_units if cu else None,
        "preferred_room_type": cu.preferred_room_type if cu else None,
    }


# ============================================================
# STUDENT: my enrollments
# ============================================================
@router.get("/me", response_model=List[EnrollmentOut])
def my_enrollments(
    academic_year: Optional[str] = None,
    semester: Optional[int] = None,
    include_dropped: bool = False,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """List the current student's enrollments."""
    if current.role != UserRole.STUDENT:
        raise HTTPException(400, "Only students can use this endpoint")

    stmt = select(Enrollment).where(Enrollment.student_id == current.id)
    if not include_dropped:
        stmt = stmt.where(Enrollment.status == "enrolled")
    if academic_year:
        stmt = stmt.where(Enrollment.academic_year == academic_year)
    if semester:
        stmt = stmt.where(Enrollment.semester == semester)
    stmt = stmt.order_by(Enrollment.module_code)

    rows = list(db.scalars(stmt))
    return [_enrich(db, e) for e in rows]


@router.post("/me", response_model=EnrollmentOut, status_code=201)
def enroll_self(
    body: EnrollmentCreate,
    cohort_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Student self-enrolls in a module. Optionally sets cohort_id on first enroll."""
    if current.role != UserRole.STUDENT:
        raise HTTPException(400, "Only students can use this endpoint")

    # If cohort_id provided and student doesn't have one yet, attach it.
    if cohort_id and not current.cohort_id:
        current.cohort_id = cohort_id
        db.commit()
        db.refresh(current)

    # Module must exist
    cu = db.get(CourseUnit, body.module_code)
    if not cu:
        raise HTTPException(404, "Module " + body.module_code + " not found")

    # Already enrolled?
    existing = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == current.id,
            Enrollment.module_code == body.module_code,
            Enrollment.academic_year == body.academic_year,
            Enrollment.semester == body.semester,
            Enrollment.status == "enrolled",
        )
    )
    if existing:
        raise HTTPException(400, "Already enrolled in " + body.module_code)

    e = Enrollment(
        student_id=current.id,
        module_code=body.module_code,
        academic_year=body.academic_year,
        semester=body.semester,
        status="enrolled",
        notes=body.notes,
    )
    db.add(e)
    db.commit()
    db.refresh(e)

    log_change(
        db, action="enroll", entity_type="enrollment",
        entity_id=e.id, user_id=current.id,
        details={"module_code": body.module_code},
    )
    db.commit()
    return _enrich(db, e)


@router.delete("/me/{module_code:path}")
def unenroll_self(
    module_code: str,
    academic_year: str = "2026/2027",
    semester: int = 1,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Student drops a module."""
    if current.role != UserRole.STUDENT:
        raise HTTPException(400, "Only students can use this endpoint")

    e = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == current.id,
            Enrollment.module_code == module_code,
            Enrollment.academic_year == academic_year,
            Enrollment.semester == semester,
            Enrollment.status == "enrolled",
        )
    )
    if not e:
        raise HTTPException(404, "Enrollment not found")
    if e.is_locked:
        raise HTTPException(400, "Enrollment is locked by admin")

    e.status = "dropped"
    e.dropped_at = datetime.utcnow()
    db.commit()

    log_change(
        db, action="drop", entity_type="enrollment",
        entity_id=e.id, user_id=current.id,
        details={"module_code": module_code},
    )
    db.commit()
    return {"status": "dropped", "module_code": module_code}


# ============================================================
# STUDENT: auto-enroll from cohort curriculum
# ============================================================
class AutoEnrollRequest(BaseModel):
    cohort_id: Optional[str] = None
    academic_year: str = "2026/2027"
    semester: int = 1


@router.post("/me/auto-enroll")
def auto_enroll_self(
    body: AutoEnrollRequest,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Auto-enroll the current student in all their cohort's curriculum units.

    Accepts cohort_id in the request body so the wizard can attach it.
    """
    if current.role != UserRole.STUDENT:
        raise HTTPException(400, "Only students can use this endpoint")

    # Attach cohort from body if not already linked
    if body.cohort_id and not current.cohort_id:
        current.cohort_id = body.cohort_id
        db.commit()
        db.refresh(current)

    academic_year = body.academic_year
    semester = body.semester

    if not current.cohort_id:
        raise HTTPException(400, "No cohort linked to this student account")

    cohort = db.get(Cohort, current.cohort_id)
    if not cohort:
        raise HTTPException(404, "Cohort not found")

    # Find all course units that match the cohort's combination (BC/MP aware)
    from app.services.auto_activity import _units_for_cohort
    units = _units_for_cohort(db, cohort, semester)

    # Filter by combination: BC students skip MP units, MP students skip BC units
    def _matches_combination(cu):
        code = cu.code.upper()
        notes = (cu.notes or "").lower()
        cohort_id = cohort.id.lower()

        # BSE-BC: takes BI (Biology) and CH (Chemistry) -- skip MT and PY
        if "bc" in cohort_id and "mp" not in cohort_id:
            if " MT " in code or " PY " in code:
                return False
        # BSE-MP: takes MT (Maths) and PY (Physics) -- skip BI and CH
        if "mp" in cohort_id and "bc" not in cohort_id:
            if " BI " in code or " CH " in code:
                return False
        return True

    units = [u for u in units if _matches_combination(u)]

    added = 0
    for cu in units:
        existing = db.scalar(
            select(Enrollment).where(
                Enrollment.student_id == current.id,
                Enrollment.module_code == cu.code,
                Enrollment.academic_year == academic_year,
                Enrollment.semester == semester,
                Enrollment.status == "enrolled",
            )
        )
        if existing:
            continue
        db.add(Enrollment(
            student_id=current.id,
            module_code=cu.code,
            academic_year=academic_year,
            semester=semester,
            status="enrolled",
            notes="Auto-enrolled from cohort curriculum",
        ))
        added += 1
    db.commit()

    log_change(
        db, action="auto_enroll", entity_type="enrollment",
        user_id=current.id,
        details={"added": added, "cohort": current.cohort_id},
    )
    db.commit()
    return {"status": "ok", "added": added, "cohort": current.cohort_id}


# ============================================================
# ADMIN: manage any student's enrollments
# ============================================================
@router.get("/student/{student_id}", response_model=List[EnrollmentOut])
def list_student_enrollments(
    student_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    rows = list(db.scalars(
        select(Enrollment).where(Enrollment.student_id == student_id)
        .order_by(Enrollment.module_code)
    ))
    return [_enrich(db, e) for e in rows]


@router.post("/student", response_model=EnrollmentOut, status_code=201)
def admin_enroll_student(
    body: AdminEnrollmentCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    """Admin enrolls a student in a module."""
    student = db.get(User, body.student_id)
    if not student or student.role != UserRole.STUDENT:
        raise HTTPException(404, "Student not found")

    cu = db.get(CourseUnit, body.module_code)
    if not cu:
        raise HTTPException(404, "Module not found")

    existing = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == body.student_id,
            Enrollment.module_code == body.module_code,
            Enrollment.academic_year == body.academic_year,
            Enrollment.semester == body.semester,
            Enrollment.status == "enrolled",
        )
    )
    if existing:
        raise HTTPException(400, "Already enrolled")

    e = Enrollment(
        student_id=body.student_id,
        module_code=body.module_code,
        academic_year=body.academic_year,
        semester=body.semester,
        status="enrolled",
        notes=body.notes,
    )
    db.add(e)
    db.commit()
    db.refresh(e)

    log_change(
        db, action="admin_enroll", entity_type="enrollment",
        entity_id=e.id, user_id=current.id,
        details={"student_id": body.student_id, "module_code": body.module_code},
    )
    db.commit()
    return _enrich(db, e)


@router.delete("/student/{enrollment_id}")
def admin_drop_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    """Admin drops an enrollment."""
    e = db.get(Enrollment, enrollment_id)
    if not e:
        raise HTTPException(404, "Enrollment not found")
    e.status = "dropped"
    e.dropped_at = datetime.utcnow()
    db.commit()

    log_change(
        db, action="admin_drop", entity_type="enrollment",
        entity_id=e.id, user_id=current.id,
    )
    db.commit()
    return {"status": "dropped"}


@router.post("/student/{enrollment_id}/lock")
def admin_lock_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    e = db.get(Enrollment, enrollment_id)
    if not e:
        raise HTTPException(404, "Enrollment not found")
    e.is_locked = True
    db.commit()
    return {"status": "locked"}


@router.post("/student/{enrollment_id}/unlock")
def admin_unlock_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    e = db.get(Enrollment, enrollment_id)
    if not e:
        raise HTTPException(404, "Enrollment not found")
    e.is_locked = False
    db.commit()
    return {"status": "unlocked"}


# ============================================================
# ADMIN: bulk-enroll a whole cohort
# ============================================================
@router.post("/bulk-cohort/{cohort_id}")
def bulk_enroll_cohort(
    cohort_id: str,
    academic_year: str = "2026/2027",
    semester: int = 1,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    """Enroll every student in a cohort in all the cohort's units."""
    cohort = db.get(Cohort, cohort_id)
    if not cohort:
        raise HTTPException(404, "Cohort not found")

    # All students in this cohort
    students = list(db.scalars(
        select(User).where(
            User.role == UserRole.STUDENT,
            User.cohort_id == cohort_id,
            User.is_active == True,  # noqa: E712
        )
    ))
    if not students:
        return {"status": "ok", "enrolled": 0, "message": "No students in cohort"}

    # Curriculum units for the cohort
    from app.services.auto_activity import _units_for_cohort
    units = _units_for_cohort(db, cohort, semester)
    if not units:
        return {"status": "ok", "enrolled": 0, "message": "No units for this cohort"}

    added = 0
    for s in students:
        for cu in units:
            existing = db.scalar(
                select(Enrollment).where(
                    Enrollment.student_id == s.id,
                    Enrollment.module_code == cu.code,
                    Enrollment.academic_year == academic_year,
                    Enrollment.semester == semester,
                    Enrollment.status == "enrolled",
                )
            )
            if existing:
                continue
            db.add(Enrollment(
                student_id=s.id,
                module_code=cu.code,
                academic_year=academic_year,
                semester=semester,
                status="enrolled",
                notes="Bulk enrollment for cohort " + cohort_id,
            ))
            added += 1
    db.commit()

    log_change(
        db, action="bulk_enroll_cohort", entity_type="enrollment",
        user_id=current.id,
        details={"cohort_id": cohort_id, "students": len(students), "added": added},
    )
    db.commit()

    return {
        "status": "ok",
        "students": len(students),
        "units": len(units),
        "enrolled": added,
    }


# ============================================================
# ADMIN: enrollment stats
# ============================================================
@router.get("/stats/student/{student_id}")
def student_enrollment_stats(
    student_id: int,
    academic_year: Optional[str] = None,
    semester: Optional[int] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    stmt = select(Enrollment).where(Enrollment.student_id == student_id)
    if academic_year:
        stmt = stmt.where(Enrollment.academic_year == academic_year)
    if semester:
        stmt = stmt.where(Enrollment.semester == semester)
    enrolled = [e for e in db.scalars(stmt) if e.status == "enrolled"]
    total_credits = 0
    for e in enrolled:
        cu = db.get(CourseUnit, e.module_code)
        if cu:
            total_credits += cu.credit_units or 0
    return {
        "student_id": student_id,
        "total_enrolled": len(enrolled),
        "total_credits": total_credits,
    }