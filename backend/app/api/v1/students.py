"""Student records API -- real university student management."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional

from app.db.session import get_db
from app.api.deps import get_current_user, require_officer
from app.models.user import User, UserRole
from app.models.student_record import StudentRecord
from app.models.programme import Programme
from app.models.cohort import Cohort
from app.core.security import hash_password
from app.services.changelog import log_change
from app.services.student_number import generate_student_number
from app.schemas.student_record import (
    StudentRecordCreate, StudentRecordUpdate, StudentRecordOut,
    BulkStudentCreate,
)
from app.schemas.common import Message


router = APIRouter(prefix="/students", tags=["students"])


# ============================================================
# SPECIAL ROUTES FIRST (before /{student_number})
# ============================================================
@router.get("/modules-for-selection")
def modules_for_selection(
    programme_code: str,
    year_level: int,
    semester: int,
    combination: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return all modules matching programme + year + semester + combination.

    Any authenticated user (including students) can call this.
    """
    from app.models.course_unit import CourseUnit, CourseUnitProgramme
    from app.services.auto_activity import (
        _extract_year_from_code, _extract_semester_from_code,
    )

    all_units = list(db.scalars(select(CourseUnit).where(CourseUnit.active == True)))  # noqa: E712

    filtered = []
    for u in all_units:
        # Programme match
        prog_match = False
        linked = db.scalar(
            select(CourseUnitProgramme).where(
                CourseUnitProgramme.course_unit_code == u.code,
                CourseUnitProgramme.programme_code == programme_code,
            )
        )
        if linked:
            prog_match = True
        else:
            first = u.code.split()[0].upper() if " " in u.code else u.code.upper()
            if first == programme_code.upper():
                prog_match = True
        if not prog_match:
            continue

        # Year match
        u_year = _extract_year_from_code(u.code)
        if u_year is not None and u_year != year_level:
            continue

        # Semester match
        u_sem = _extract_semester_from_code(u.code)
        if u_sem is not None and u_sem != semester:
            continue

        # Combination filter (BC/MP)
        if combination:
            combo = combination.upper()
            code = u.code.upper()
            if combo == "BC":
                if " MT " in code or " PY " in code:
                    continue
            elif combo == "MP":
                if " BI " in code or " CH " in code:
                    continue

        filtered.append(u)

    filtered.sort(key=lambda x: x.code)

    return [
        {
            "code": u.code,
            "name": u.name,
            "credit_units": u.credit_units,
            "contact_hours_per_week": u.contact_hours_per_week,
            "preferred_room_type": u.preferred_room_type,
            "is_cross_cutting": u.is_cross_cutting,
            "owning_school": u.owning_school,
        }
        for u in filtered
    ]


@router.get("/stats/summary")
def students_summary(
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    """Counts by programme, year, status."""
    all_students = list(db.scalars(select(StudentRecord)))

    by_programme = {}
    by_year = {}
    by_status = {}
    by_combination = {}

    for s in all_students:
        by_programme[s.programme_code] = by_programme.get(s.programme_code, 0) + 1
        by_year[s.year_level] = by_year.get(s.year_level, 0) + 1
        by_status[s.status] = by_status.get(s.status, 0) + 1
        if s.combination:
            by_combination[s.combination] = by_combination.get(s.combination, 0) + 1

    return {
        "total": len(all_students),
        "by_programme": by_programme,
        "by_year": by_year,
        "by_status": by_status,
        "by_combination": by_combination,
    }


# ============================================================
# GENERIC /{student_number} LAST
# ============================================================
@router.get("", response_model=List[StudentRecordOut])
def list_students(
    programme_code: Optional[str] = None,
    year_level: Optional[int] = None,
    semester: Optional[int] = None,
    combination: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    stmt = select(StudentRecord)
    if programme_code:
        stmt = stmt.where(StudentRecord.programme_code == programme_code)
    if year_level:
        stmt = stmt.where(StudentRecord.year_level == year_level)
    if semester:
        stmt = stmt.where(StudentRecord.semester == semester)
    if combination:
        stmt = stmt.where(StudentRecord.combination == combination)
    if status:
        stmt = stmt.where(StudentRecord.status == status)
    stmt = stmt.order_by(StudentRecord.student_number)
    return [_enrich(db, sr) for sr in db.scalars(stmt)]


def _enrich(db: Session, sr: StudentRecord) -> dict:
    user = db.get(User, sr.user_id)
    prog = db.get(Programme, sr.programme_code)
    return {
        "id": sr.id,
        "user_id": sr.user_id,
        "student_number": sr.student_number,
        "programme_code": sr.programme_code,
        "year_level": sr.year_level,
        "semester": sr.semester,
        "intake": sr.intake,
        "academic_year": sr.academic_year,
        "combination": sr.combination,
        "mode": sr.mode,
        "status": sr.status,
        "phone": sr.phone,
        "guardian_name": sr.guardian_name,
        "guardian_phone": sr.guardian_phone,
        "notes": sr.notes,
        "email": user.email if user else None,
        "full_name": user.full_name if user else None,
        "programme_name": prog.name if prog else None,
    }


def _validate_combination(programme_code: str, combination: Optional[str]) -> None:
    if not combination:
        return
    if programme_code.upper() != "BSE":
        raise HTTPException(400, f"Combination only applies to BSE")
    if combination.upper() not in ("BC", "MP"):
        raise HTTPException(400, "Invalid combination. Must be BC or MP.")


@router.get("/{student_number}", response_model=StudentRecordOut)
def get_student(
    student_number: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_officer),
):
    sr = db.scalar(select(StudentRecord).where(StudentRecord.student_number == student_number))
    if not sr:
        raise HTTPException(404, "Student not found")
    return _enrich(db, sr)


@router.post("", response_model=StudentRecordOut, status_code=201)
def create_student(
    body: StudentRecordCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    if not db.get(Programme, body.programme_code):
        raise HTTPException(404, "Programme not found")
    _validate_combination(body.programme_code, body.combination)
    if db.scalar(select(User).where(User.email == body.email)):
        raise HTTPException(400, "Email already registered")

    student_number = body.student_number or generate_student_number(db)
    if db.scalar(select(StudentRecord).where(StudentRecord.student_number == student_number)):
        raise HTTPException(400, "Student number already exists")

    user = User(
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        role=UserRole.STUDENT,
        is_active=True,
    )
    db.add(user)
    db.flush()

    sr = StudentRecord(
        user_id=user.id,
        student_number=student_number,
        programme_code=body.programme_code,
        year_level=body.year_level,
        semester=body.semester,
        intake=body.intake,
        academic_year=body.academic_year,
        combination=body.combination,
        mode=body.mode,
        status=body.status,
        phone=body.phone,
        guardian_name=body.guardian_name,
        guardian_phone=body.guardian_phone,
        notes=body.notes,
    )
    db.add(sr)
    db.commit()
    db.refresh(sr)

    log_change(db, action="student_created", entity_type="student_record",
               entity_id=sr.id, user_id=current.id,
               details={"student_number": student_number})
    db.commit()
    return _enrich(db, sr)


@router.patch("/{student_id}", response_model=StudentRecordOut)
def update_student(
    student_id: int,
    body: StudentRecordUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    sr = db.get(StudentRecord, student_id)
    if not sr:
        raise HTTPException(404, "Student not found")
    data = body.model_dump(exclude_unset=True)
    new_prog = data.get("programme_code", sr.programme_code)
    new_comb = data.get("combination", sr.combination)
    if "programme_code" in data or "combination" in data:
        _validate_combination(new_prog, new_comb)
    for k, v in data.items():
        setattr(sr, k, v)
    db.commit()
    db.refresh(sr)
    log_change(db, action="student_updated", entity_type="student_record",
               entity_id=sr.id, user_id=current.id)
    db.commit()
    return _enrich(db, sr)


@router.delete("/{student_id}", response_model=Message)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    sr = db.get(StudentRecord, student_id)
    if not sr:
        raise HTTPException(404, "Student not found")
    sr.status = "Inactive"
    user = db.get(User, sr.user_id)
    if user:
        user.is_active = False
    db.commit()
    log_change(db, action="student_deactivated", entity_type="student_record",
               entity_id=sr.id, user_id=current.id)
    db.commit()
    return Message(detail=f"Student {sr.student_number} deactivated")


@router.post("/bulk", status_code=201)
def bulk_create_students(
    body: BulkStudentCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_officer),
):
    created = 0
    errors = []
    for i, s in enumerate(body.students):
        try:
            if not db.get(Programme, s.programme_code):
                errors.append(f"Row {i+1}: programme not found")
                continue
            _validate_combination(s.programme_code, s.combination)
            if db.scalar(select(User).where(User.email == s.email)):
                errors.append(f"Row {i+1}: email exists")
                continue
            student_number = s.student_number or generate_student_number(db)
            user = User(
                email=s.email, full_name=s.full_name,
                hashed_password=hash_password(s.password),
                role=UserRole.STUDENT, is_active=True,
            )
            db.add(user)
            db.flush()
            sr = StudentRecord(
                user_id=user.id, student_number=student_number,
                programme_code=s.programme_code, year_level=s.year_level,
                semester=s.semester, intake=s.intake, academic_year=s.academic_year,
                combination=s.combination, mode=s.mode, status=s.status,
                phone=s.phone, guardian_name=s.guardian_name,
                guardian_phone=s.guardian_phone, notes=s.notes,
            )
            db.add(sr)
            created += 1
        except HTTPException as e:
            errors.append(f"Row {i+1}: {e.detail}")
        except Exception as e:
            errors.append(f"Row {i+1}: {str(e)}")
    db.commit()
    log_change(db, action="bulk_students_created", entity_type="student_record",
               user_id=current.id, details={"created": created, "errors": len(errors)})
    db.commit()
    return {"status": "ok", "created": created, "errors": errors}