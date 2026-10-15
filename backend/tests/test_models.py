"""Test database models."""
from app.models.programme import Programme
from app.models.cohort import Cohort
from app.models.course_unit import CourseUnit
from app.models.lecturer import Lecturer
from app.models.room import Room


def test_create_programme(db):
    p = Programme(code="T1", name="Test", level="Bachelor",
                  school_faculty="S", duration_years=3, active=True)
    db.add(p); db.commit()
    assert db.get(Programme, "T1").name == "Test"


def test_create_cohort(db):
    db.add(Programme(code="T1", name="P", level="Bachelor",
                     school_faculty="S", duration_years=3, active=True))
    db.commit()
    c = Cohort(id="T1-Y1-Day", programme_code="T1", year_level=1, mode="Day",
               intake="Aug", academic_year="2026/2027", semester=1,
               estimated_students=30, status="Active")
    db.add(c); db.commit()
    assert c.id == "T1-Y1-Day"


def test_course_unit_room_type(db):
    cu = CourseUnit(code="T1 XX 71101", name="U", credit_units=3,
                    contact_hours_per_week=2, normal_year=1, is_cross_cutting=False,
                    preferred_room_type="Lecture", active=True)
    db.add(cu); db.commit()
    assert cu.preferred_room_type == "Lecture"


def test_lecturer_defaults(db):
    l = Lecturer(id="L1", full_name="Dr X", max_hours_per_week=16,
                 preferred_mode="Both", active=True)
    db.add(l); db.commit()
    assert l.max_hours_per_week == 16


def test_room_capacity(db):
    r = Room(code="R1", name="Room 1", capacity=40,
             room_type="Lecture", available_modes="Both", active=True)
    db.add(r); db.commit()
    assert r.capacity == 40