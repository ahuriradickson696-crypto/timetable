"""Test the timetable solver."""
from app.services.solver.model_builder import TimetableModel, SolverInput


def _sample():
    return SolverInput(
        activities=[
            {"id": "A1", "cohort_id": "C1", "module_code": "M1", "lecturer_id": "L1",
             "duration_periods": 1, "preferred_room_type": "Lecture", "students": 30,
             "split_allowed": False, "joint_cohort_ids": None, "activity_type": "teaching"},
            {"id": "A2", "cohort_id": "C2", "module_code": "M2", "lecturer_id": "L2",
             "duration_periods": 1, "preferred_room_type": "Lecture", "students": 30,
             "split_allowed": False, "joint_cohort_ids": None, "activity_type": "teaching"},
        ],
        cohorts=[
            {"id": "C1", "mode": "Day", "estimated_students": 30},
            {"id": "C2", "mode": "Day", "estimated_students": 30},
        ],
        rooms=[{"code": "R1", "capacity": 40, "room_type": "Lecture", "available_modes": "Both"}],
        periods=[
            {"id": 1, "period_id": "P1", "day": "Monday", "start_time": "08:00",
             "end_time": "09:00", "mode": "Day", "is_break": False, "order_index": 1},
            {"id": 2, "period_id": "P2", "day": "Monday", "start_time": "09:00",
             "end_time": "10:00", "mode": "Day", "is_break": False, "order_index": 2},
        ],
        lecturers=[
            {"id": "L1", "max_hours_per_week": 16, "preferred_mode": "Both", "unavailable_days": None},
            {"id": "L2", "max_hours_per_week": 16, "preferred_mode": "Both", "unavailable_days": None},
        ],
    )


def test_solver_places_all():
    model = TimetableModel(_sample(), run_type="teaching")
    out = model.solve(time_limit=10)
    assert out.status in ("optimal", "feasible")
    assert len(out.assignments) == 2


def test_solver_detects_impossible_capacity():
    data = _sample()
    data.rooms = [{"code": "TINY", "capacity": 5, "room_type": "Lecture", "available_modes": "Both"}]
    model = TimetableModel(data, run_type="teaching")
    out = model.solve(time_limit=5)
    assert out.status == "infeasible"


def test_solver_skips_activities_with_only_break_periods():
    """When only break periods exist, no assignments should be made."""
    data = _sample()
    data.periods = [
        {"id": 1, "period_id": "P1", "day": "Monday", "start_time": "08:00",
         "end_time": "09:00", "mode": "Day", "is_break": True, "order_index": 1},
    ]
    model = TimetableModel(data, run_type="teaching")
    out = model.solve(time_limit=5)
    # No teaching periods exist, so nothing gets scheduled
    assert len(out.assignments) == 0