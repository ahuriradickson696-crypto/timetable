from app.db.session import SessionLocal
from app.models.cohort import Cohort
from app.models.course_unit import CourseUnit
from app.models.activity import Activity
from app.models.lecturer import Lecturer


def lecturer_for(module_code):
    code = module_code.upper()
    if " CS " in code or " IT " in code: return "LECT-004"
    if " BI " in code: return "LECT-005"
    if " CH " in code: return "LECT-006"
    if " MT " in code: return "LECT-007"
    if " PY " in code: return "LECT-008"
    if " AP " in code: return "LECT-010"
    if " BC " in code: return "LECT-011"
    if " MB " in code: return "LECT-012"
    if " CM " in code: return "LECT-016"
    if " CP " in code: return "LECT-017"
    if " LB " in code: return "LECT-018"
    if " HE " in code: return "LECT-020"
    if " ED " in code: return "LECT-002"
    return "LECT-001"


db = SessionLocal()
cohorts = db.query(Cohort).all()
created = 0
for cohort in cohorts:
    prefix = cohort.programme_code + " %"
    units = db.query(CourseUnit).filter(
        CourseUnit.code.like(prefix),
        CourseUnit.normal_year == cohort.year_level,
        CourseUnit.active == True,
    ).all()

    if cohort.programme_code == "BSE":
        if "-BC-" in cohort.id:
            units = [u for u in units if "BC" in (u.notes or "") or u.is_cross_cutting or (" BI " in u.code or " CH " in u.code)]
        elif "-MP-" in cohort.id:
            units = [u for u in units if "MP" in (u.notes or "") or u.is_cross_cutting or (" MT " in u.code or " PY " in u.code)]

    for u in units:
        exists = db.query(Activity).filter(
            Activity.cohort_id == cohort.id,
            Activity.module_code == u.code,
            Activity.semester == cohort.semester,
            Activity.academic_year == cohort.academic_year,
        ).first()
        if exists:
            continue
        lect = lecturer_for(u.code)
        if not db.query(Lecturer).filter(Lecturer.id == lect).first():
            lect = "LECT-001"
        act_id = cohort.id + "--" + u.code.replace(" ", "_")
        act = Activity(
            id=act_id,
            cohort_id=cohort.id,
            module_code=u.code,
            lecturer_id=lect,
            duration_periods=max(1, u.contact_hours_per_week // 2),
            preferred_room_type=u.preferred_room_type,
            students=cohort.estimated_students or 30,
            split_allowed=False,
            semester=cohort.semester,
            intake=cohort.intake,
            academic_year=cohort.academic_year,
            activity_type="teaching",
            notes="",
        )
        db.add(act)
        created += 1

db.commit()
total = db.query(Activity).count()
print("Created " + str(created) + " new activities. Total activities now: " + str(total))
db.close()