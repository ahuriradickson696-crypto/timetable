"""ONE COMMAND FIX. Drops the DB, recreates it, seeds everything."""
import sys, os

ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, ROOT)

# ---- Delete old DB
db_path = os.path.join(ROOT, "aviu_timetable.db")
if os.path.exists(db_path):
    os.remove(db_path)
    print("Deleted old DB")

# ---- Import after deleting so fresh connections are used
from app.db.session import SessionLocal, engine
from app.db.base import Base
import app.models  # noqa
from app.models.user import User, UserRole
from app.models.programme import Programme
from app.models.cohort import Cohort
from app.models.course_unit import CourseUnit
from app.models.lecturer import Lecturer
from app.models.room import Room
from app.models.time_period import TimePeriod
from app.models.student_record import StudentRecord
from app.models.enrollment import Enrollment
from app.core.security import hash_password

# ---- Create all tables
Base.metadata.create_all(bind=engine)
print("Created tables")

db = SessionLocal()

try:
    # ============ PROGRAMS ============
    db.add_all([
        Programme(code="BSE", name="Bachelor of Science with Education",
                  level="Bachelor", school_faculty="School of Education",
                  duration_years=3, active=True, notes=""),
        Programme(code="DCM", name="Diploma in Clinical Medicine and Community Health",
                  level="Diploma", school_faculty="School of Health Sciences",
                  duration_years=3, active=True, notes=""),
        Programme(code="DMLT", name="Diploma in Medical Laboratory",
                  level="Diploma", school_faculty="School of Health Sciences",
                  duration_years=2, active=True, notes=""),
    ])
    db.commit()
    print(f"Programmes: {db.query(Programme).count()}")

    # ============ COHORTS ============
    db.add_all([
        Cohort(id="BSE-BC-Y1-Day-Aug2026", programme_code="BSE", year_level=1, mode="Day",
               intake="Aug", academic_year="2026/2027", semester=1,
               estimated_students=30, status="Active"),
        Cohort(id="BSE-MP-Y1-Day-Aug2026", programme_code="BSE", year_level=1, mode="Day",
               intake="Aug", academic_year="2026/2027", semester=1,
               estimated_students=30, status="Active"),
        Cohort(id="DCM-Y1-Day-Aug2026", programme_code="DCM", year_level=1, mode="Day",
               intake="Aug", academic_year="2026/2027", semester=1,
               estimated_students=40, status="Active"),
        Cohort(id="DMLT-Y1-Day-Aug2026", programme_code="DMLT", year_level=1, mode="Day",
               intake="Aug", academic_year="2026/2027", semester=1,
               estimated_students=30, status="Active"),
    ])
    db.commit()
    print(f"Cohorts: {db.query(Cohort).count()}")

    # ============ COURSE UNITS (BSE Year 1 Semester 1 BC + MP) ============
    units = [
        # Common BSE units
        ("BSE ED 71101", "Foundations of Education", 3, "Lecture", True),
        ("BSE ED 71102", "Human Growth and Development", 3, "Lecture", True),
        ("BSE CS 71103", "Communication Skills", 2, "Lecture", True),
        ("BSE IT 71104", "Computer Applications", 2, "Computer Lab", True),
        # BC-specific
        ("BSE BI 71105", "Cell Biology and Genetics", 3, "Lecture", False),
        ("BSE BI 71106", "Biology Practicals I", 1, "Science Lab", False),
        ("BSE CH 71107", "General and Inorganic Chemistry I", 3, "Lecture", False),
        ("BSE CH 71108", "Chemistry Practicals I", 1, "Science Lab", False),
        # MP-specific
        ("BSE MT 71109", "Calculus I", 3, "Lecture", False),
        ("BSE MT 71110", "Algebra I", 3, "Lecture", False),
        ("BSE PY 71111", "Mechanics and Properties of Matter", 3, "Lecture", False),
        ("BSE PY 71112", "Physics Practicals I", 1, "Science Lab", False),
        # DCM
        ("DCM CS 51101", "Communication Skills", 2, "Lecture", True),
        ("DCM IT 51102", "Basic Computer Skills", 2, "Computer Lab", True),
        ("DCM AP 51103", "Human Anatomy and Physiology I", 4, "Lecture", True),
        ("DCM BC 51104", "Medical Biochemistry I", 3, "Lecture", False),
        ("DCM MB 51105", "Medical Microbiology I", 3, "Lecture", False),
        ("DCM CM 51106", "Introduction to Community Health", 3, "Lecture", False),
        ("DCM CP 51107", "Clinical Skills I", 3, "Clinical Lab", False),
        ("DCM HE 51108", "Health Ethics and Professionalism", 2, "Lecture", False),
        # DMLT
        ("DMLT CS 51101", "Communication Skills", 2, "Lecture", True),
        ("DMLT IT 51102", "Basic Computer Skills", 2, "Computer Lab", True),
        ("DMLT AP 51103", "Human Anatomy and Physiology I", 4, "Lecture", True),
        ("DMLT LB 51104", "Intro to Medical Lab Practice", 3, "Science Lab", False),
        ("DMLT MB 51105", "Medical Microbiology I", 4, "Science Lab", False),
        ("DMLT CC 51106", "Clinical Chemistry I", 3, "Science Lab", False),
        ("DMLT HM 51107", "Haematology I", 3, "Science Lab", False),
    ]
    for code, name, cu, room, cross in units:
        db.add(CourseUnit(
            code=code, name=name, credit_units=cu,
            contact_hours_per_week=cu, normal_year=1,
            is_cross_cutting=cross, preferred_room_type=room,
            active=True, notes="Common to both BSE teaching combinations" if cross else "",
        ))
    db.commit()
    print(f"Course units: {db.query(CourseUnit).count()}")

    # ============ LECTURERS ============
    lecturers = [
        ("LECT-001", "Baron Esau Turyatemba", 20, "Day", "IT Officer"),
        ("LECT-002", "Dr. Jane Nakato (Education)", 16, "Both", "Education"),
        ("LECT-003", "Prof. Sarah Achieng (Curriculum)", 16, "Both", "Education"),
        ("LECT-004", "Lecturer in Communication Skills", 16, "Both", "Communication"),
        ("LECT-005", "Lecturer in Biology", 16, "Both", "Biology"),
        ("LECT-006", "Lecturer in Chemistry", 16, "Both", "Chemistry"),
        ("LECT-007", "Lecturer in Mathematics", 16, "Both", "Mathematics"),
        ("LECT-008", "Lecturer in Physics", 16, "Both", "Physics"),
        ("LECT-010", "Lecturer in Anatomy and Physiology", 16, "Both", "Health"),
        ("LECT-011", "Lecturer in Biochemistry", 16, "Both", "Health"),
        ("LECT-012", "Lecturer in Microbiology", 16, "Both", "Health"),
        ("LECT-016", "Lecturer in Community Health", 16, "Both", "Health"),
        ("LECT-017", "Clinical Skills Instructor", 16, "Both", "Clinical"),
        ("LECT-018", "Medical Laboratory Scientist", 16, "Both", "Lab"),
        ("LECT-020", "Lecturer in Ethics", 16, "Both", "Ethics"),
        ("LECT-021", "Lecturer in ICT for Education", 16, "Both", "ICT"),
    ]
    for lid, name, hrs, mode, note in lecturers:
        db.add(Lecturer(id=lid, full_name=name, max_hours_per_week=hrs,
                       preferred_mode=mode, active=True, notes=note))
    db.commit()
    print(f"Lecturers: {db.query(Lecturer).count()}")

    # ============ ROOMS ============
    rooms = [
        ("MH-01", "Main Hall", 150, "Lecture"),
        ("CR-01", "Classroom 1", 80, "Lecture"),
        ("CR-02", "Classroom 2", 80, "Lecture"),
        ("CR-03", "Classroom 3", 60, "Lecture"),
        ("CR-04", "Classroom 4", 50, "Lecture"),
        ("CL-01", "Computer Lab 1", 40, "Computer Lab"),
        ("CL-02", "Computer Lab 2", 40, "Computer Lab"),
        ("SL-BIO", "Biology Lab", 35, "Science Lab"),
        ("SL-CHM", "Chemistry Lab", 35, "Science Lab"),
        ("SL-PHY", "Physics Lab", 35, "Science Lab"),
        ("ML-01", "Medical Lab 1", 35, "Science Lab"),
        ("ML-02", "Medical Lab 2", 35, "Science Lab"),
        ("CS-LAB", "Clinical Skills Lab", 40, "Clinical Lab"),
    ]
    for code, name, cap, rtype in rooms:
        db.add(Room(code=code, name=name, capacity=cap, room_type=rtype,
                   available_modes="Both", active=True))
    db.commit()
    print(f"Rooms: {db.query(Room).count()}")

    # ============ TIME PERIODS ============
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    slots = [("P1", "08:00", "09:00"), ("P2", "09:00", "10:00"),
             ("P3", "11:00", "12:00"), ("P4", "12:00", "13:00"),
             ("P5", "14:00", "15:00"), ("P6", "15:00", "16:00")]
    for day_idx, day in enumerate(days):
        for slot_idx, (pid, start, end) in enumerate(slots):
            db.add(TimePeriod(
                period_id=pid, day=day, start_time=start, end_time=end,
                mode="Day", is_break=False, order_index=day_idx * 100 + slot_idx,
            ))
    db.commit()
    print(f"Time periods: {db.query(TimePeriod).count()}")

    # ============ ADMIN USER ============
    db.add(User(
        email="admin@aviu.ac.ug", full_name="System Administrator",
        hashed_password=hash_password("admin123"),
        role=UserRole.ADMIN, is_active=True,
    ))
    db.commit()
    print("Admin created")

    # ============ STUDENT USER + RECORD ============
    stu = User(
        email="student1@aviu.ac.ug", full_name="Test Student BSE-BC",
        hashed_password=hash_password("student123"),
        role=UserRole.STUDENT, cohort_id="BSE-BC-Y1-Day-Aug2026",
        is_active=True,
    )
    db.add(stu)
    db.commit()
    db.refresh(stu)

    sr = StudentRecord(
        user_id=stu.id, student_number="AVIU/2026/0001",
        programme_code="BSE", year_level=1, semester=1,
        intake="Aug", academic_year="2026/2027",
        combination="BC", mode="Day", status="Active",
    )
    db.add(sr)
    db.commit()
    print("Student created + record linked")

    # ============ LECTURER USER ============
    db.add(User(
        email="lecturer1@aviu.ac.ug", full_name="Dr. Jane Nakato",
        hashed_password=hash_password("lecturer123"),
        role=UserRole.LECTURER, lecturer_id="LECT-002",
        is_active=True,
    ))
    db.commit()
    print("Lecturer created")

    # ============ ENROLL STUDENT IN BC MODULES ============
    bc_modules = [
        "BSE ED 71101", "BSE ED 71102", "BSE CS 71103", "BSE IT 71104",
        "BSE BI 71105", "BSE BI 71106", "BSE CH 71107", "BSE CH 71108",
    ]
    for code in bc_modules:
        db.add(Enrollment(
            student_id=stu.id, module_code=code,
            academic_year="2026/2027", semester=1, status="enrolled",
        ))
    db.commit()
    print(f"Enrolled student in {len(bc_modules)} BC modules")

    # ============ SUMMARY ============
    print()
    print("=" * 60)
    print("DATABASE READY")
    print("=" * 60)
    print(f"  Programmes:   {db.query(Programme).count()}")
    print(f"  Cohorts:      {db.query(Cohort).count()}")
    print(f"  Course Units: {db.query(CourseUnit).count()}")
    print(f"  Lecturers:    {db.query(Lecturer).count()}")
    print(f"  Rooms:        {db.query(Room).count()}")
    print(f"  Time Periods: {db.query(TimePeriod).count()}")
    print(f"  Enrollments:  {db.query(Enrollment).count()}")
    print()
    print("LOGINS:")
    print("  Admin:    admin@aviu.ac.ug / admin123")
    print("  Student:  student1@aviu.ac.ug / student123")
    print("  Lecturer: lecturer1@aviu.ac.ug / lecturer123")
    print("=" * 60)

finally:
    db.close()
