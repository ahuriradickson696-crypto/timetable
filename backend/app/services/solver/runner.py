"""High-level runner: fetch data, run solver, persist results."""
import json
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.activity import Activity
from app.models.cohort import Cohort
from app.models.room import Room
from app.models.time_period import TimePeriod
from app.models.lecturer import Lecturer
from app.models.timetable import TimetableRun, TimetableAssignment
from app.services.solver.model_builder import TimetableModel, SolverInput
from app.config import settings
from app.core.logging import logger


# Map run_type -> time grid mode
GRID_MODE = {
    "teaching": "Day",
    "test": "Test",
    "exam": "Exam",
}

# Map run_type -> activity_type
ACTIVITY_TYPE = {
    "teaching": "teaching",
    "test": "test",
    "exam": "exam",
}


def generate_timetable(
    db: Session,
    intake: str = "Aug",
    academic_year: str = "2026/2027",
    semester: int = 1,
    run_type: str = "teaching",
    created_by: Optional[int] = None,
    time_limit: Optional[int] = None,
    seed: Optional[int] = None,
) -> TimetableRun:

    if run_type not in GRID_MODE:
        raise ValueError(f"Invalid run_type: {run_type}. Must be teaching | test | exam")

    grid_mode = GRID_MODE[run_type]
    act_type = ACTIVITY_TYPE[run_type]

    run = TimetableRun(
        intake=intake,
        academic_year=academic_year,
        semester=semester,
        run_type=run_type,
        status="running",
        solver_params=json.dumps({
            "time_limit": time_limit or settings.SOLVER_TIME_LIMIT_SECONDS,
            "workers": settings.SOLVER_NUM_WORKERS,
            "seed": seed if seed is not None else settings.SOLVER_RANDOM_SEED,
            "run_type": run_type,
        }),
        created_by=created_by,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        # Load activities filtered by type
        activities = list(db.scalars(select(Activity).where(
            Activity.semester == semester,
            Activity.intake == intake,
            Activity.academic_year == academic_year,
            Activity.activity_type == act_type,
        )))
        if not activities:
            raise ValueError(
                f"No {run_type} activities found for {intake} {academic_year} Sem {semester}"
            )

        cohorts = list(db.scalars(select(Cohort).where(Cohort.status == "Active")))
        rooms = list(db.scalars(select(Room).where(Room.active == True)))  # noqa: E712
        # Filter time periods by grid mode
        periods = list(db.scalars(
            select(TimePeriod)
            .where(TimePeriod.mode == grid_mode)
            .order_by(TimePeriod.order_index)
        ))
        lecturers = list(db.scalars(select(Lecturer).where(Lecturer.active == True)))  # noqa: E712

        logger.info(
            f"Generating {run_type} run #{run.id}: "
            f"{len(activities)} activities, {len(rooms)} rooms, {len(periods)} {grid_mode} periods"
        )

        data = SolverInput(
            activities=[{
                "id": a.id,
                "cohort_id": a.cohort_id,
                "module_code": a.module_code,
                "lecturer_id": a.lecturer_id,
                "duration_periods": a.duration_periods,
                "preferred_room_type": a.preferred_room_type,
                "students": a.students,
                "split_allowed": a.split_allowed,
                "joint_cohort_ids": a.joint_cohort_ids,
                "activity_type": a.activity_type,
            } for a in activities],
            cohorts=[{"id": c.id, "mode": c.mode, "estimated_students": c.estimated_students} for c in cohorts],
            rooms=[{"code": r.code, "capacity": r.capacity, "room_type": r.room_type, "available_modes": r.available_modes} for r in rooms],
            periods=[{
                "id": p.id,
                "period_id": p.period_id,
                "day": p.day,
                "start_time": p.start_time,
                "end_time": p.end_time,
                "mode": p.mode,
                "is_break": p.is_break,
                "order_index": p.order_index,
            } for p in periods],
            lecturers=[{
                "id": l.id,
                "max_hours_per_week": l.max_hours_per_week,
                "preferred_mode": l.preferred_mode,
                "unavailable_days": l.unavailable_days,
            } for l in lecturers],
        )

        model = TimetableModel(data, run_type=run_type)
        output = model.solve(time_limit=time_limit, seed=seed)

        if output.status not in ("optimal", "feasible"):
            run.status = "failed"
            run.message = f"Solver returned: {output.status}"
            run.metrics = json.dumps({
                "wall_time": output.wall_time,
                "objective": output.objective_value,
                "status": output.status,
            })
            db.commit()
            db.refresh(run)
            return run

        for a in output.assignments:
            db.add(TimetableAssignment(
                run_id=run.id,
                activity_id=a["activity_id"],
                period_id=a["period_id"],
                room_code=a["room_code"],
                split_group=a["split_group"],
            ))

        run.status = "success"
        run.message = f"Scheduled {len(output.assignments)} {run_type} activities"
        run.metrics = json.dumps({
            "wall_time": output.wall_time,
            "objective": output.objective_value,
            "status": output.status,
            "assignments": len(output.assignments),
        })
        db.commit()
        db.refresh(run)
        logger.info(f"Run {run.id} ({run_type}) completed: {run.message}")
        return run

    except Exception as e:
        logger.exception("Solver run failed")
        run.status = "failed"
        run.message = str(e)
        db.commit()
        db.refresh(run)
        return run