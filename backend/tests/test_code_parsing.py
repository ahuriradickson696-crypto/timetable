"""Test module code parsers."""
from app.services.auto_activity import (
    _extract_year_from_code, _extract_semester_from_code,
    _cohort_slug, _is_common_to_multiple_cohorts,
)
from app.models.course_unit import CourseUnit


def test_parse_year():
    assert _extract_year_from_code("BSE ED 71101") == 1
    assert _extract_year_from_code("BSE ED 71201") == 1
    assert _extract_year_from_code("DCM AP 52101") == 2
    assert _extract_year_from_code("BSE MT 73111") == 3
    assert _extract_year_from_code("invalid") is None


def test_parse_semester():
    assert _extract_semester_from_code("BSE ED 71101") == 1
    assert _extract_semester_from_code("BSE ED 71201") == 2
    assert _extract_semester_from_code("DCM AP 52101") == 1


def test_cohort_slugs_unique():
    a = _cohort_slug("BSE-BC-Y1-Day-Aug2026")
    b = _cohort_slug("BSE-MP-Y1-Day-Aug2026")
    c = _cohort_slug("DCM-Y1-Day-Aug2026")
    d = _cohort_slug("DMLT-Y1-Day-Aug2026")
    assert a != b
    assert c != d
    assert a != c


def test_is_common_detects_notes():
    u1 = CourseUnit(code="T", name="T", credit_units=1, contact_hours_per_week=1,
                    normal_year=1, is_cross_cutting=True, preferred_room_type="Lecture",
                    active=True, notes="Common to both BSE teaching combinations")
    assert _is_common_to_multiple_cohorts(u1) is True

    u2 = CourseUnit(code="T", name="T", credit_units=1, contact_hours_per_week=1,
                    normal_year=1, is_cross_cutting=False, preferred_room_type="Lecture",
                    active=True, notes="Practical session in laboratory")
    assert _is_common_to_multiple_cohorts(u2) is False