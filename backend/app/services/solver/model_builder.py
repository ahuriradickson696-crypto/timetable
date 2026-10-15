"""Build the CP-SAT model for AVIU timetabling."""
from ortools.sat.python import cp_model
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from app.config import settings
from app.core.logging import logger


@dataclass
class SolverInput:
    activities: List[dict]
    cohorts: List[dict]
    rooms: List[dict]
    periods: List[dict]
    lecturers: List[dict]


@dataclass
class SolverOutput:
    status: str
    assignments: List[dict]
    objective_value: float
    wall_time: float
    message: str


class TimetableModel:
    def __init__(self, data: SolverInput, run_type: str = "teaching"):
        self.data = data
        self.run_type = run_type
        self.model = cp_model.CpModel()
        self.x: Dict[Tuple[str, int, str], cp_model.IntVar] = {}
        # y[(activity_id,)] = the chosen period id (IntVar)
        self.y: Dict[str, cp_model.IntVar] = {}
        self._build()

    def _build(self) -> None:
        self._create_variables()
        self._add_hard_constraints()
        self._add_soft_constraints()

    # ------------------------------------------------------------
    # Variables
    # ------------------------------------------------------------
    def _create_variables(self) -> None:
        for a in self.data.activities:
            aid = a["id"]
            if a.get("duration_periods", 0) == 0:
                continue
            for p in self.data.periods:
                if p["is_break"]:
                    continue
                for r in self.data.rooms:
                    key = (aid, p["id"], r["code"])
                    var_name = "x_" + str(aid) + "_" + str(p["id"]) + "_" + str(r["code"])
                    self.x[key] = self.model.NewBoolVar(var_name)

        # y[aid] = the start period id (only if activity has candidate periods)
        period_ids = [p["id"] for p in self.data.periods if not p["is_break"]]
        for a in self.data.activities:
            aid = a["id"]
            if a.get("duration_periods", 0) == 0:
                continue
            has_any = any((aid, pid, r["code"]) in self.x for pid in period_ids for r in self.data.rooms)
            if not has_any:
                continue
            y = self.model.NewIntVar(min(period_ids), max(period_ids), "y_" + str(aid))
            self.y[aid] = y
            for p in self.data.periods:
                if p["is_break"]:
                    continue
                matching = [v for (aid_k, pid, _), v in self.x.items() if aid_k == aid and pid == p["id"]]
                if matching:
                    # at_p = 1 if activity is scheduled at this period, 0 otherwise
                    at_p = self.model.NewBoolVar("at_" + str(aid) + "_" + str(p["id"]))
                    self.model.Add(sum(matching) == at_p)
                    # If at this period, then y == period id
                    self.model.Add(y == p["id"]).OnlyEnforceIf(at_p)

    # ------------------------------------------------------------
    # Hard constraints
    # ------------------------------------------------------------
    def _add_hard_constraints(self) -> None:
        self._c_each_activity_scheduled_once()
        self._c_no_lecturer_clash()
        self._c_no_room_clash()
        self._c_no_cohort_clash()
        self._c_capacity()
        self._c_breaks_excluded()
        self._c_lab_rooms()
        if self.run_type in ("test", "exam"):
            self._c_one_exam_per_day()

    def _c_each_activity_scheduled_once(self) -> None:
        for a in self.data.activities:
            aid = a["id"]
            if a.get("duration_periods", 0) == 0:
                continue
            vars_for_a = [v for (aid_k, _, _), v in self.x.items() if aid_k == aid]
            if vars_for_a:
                self.model.Add(sum(vars_for_a) == 1)

    def _c_no_lecturer_clash(self) -> None:
        lect_acts: Dict[str, List[str]] = {}
        for a in self.data.activities:
            if a.get("duration_periods", 0) == 0:
                continue
            lect_acts.setdefault(a["lecturer_id"], []).append(a["id"])
        for lect_id, act_ids in lect_acts.items():
            for p in self.data.periods:
                vars_here = [v for (aid, pid, _), v in self.x.items() if aid in act_ids and pid == p["id"]]
                if len(vars_here) > 1:
                    self.model.Add(sum(vars_here) <= 1)

    def _c_no_room_clash(self) -> None:
        for r in self.data.rooms:
            rcode = r["code"]
            for p in self.data.periods:
                vars_here = [v for (_, pid, rc), v in self.x.items() if pid == p["id"] and rc == rcode]
                if len(vars_here) > 1:
                    self.model.Add(sum(vars_here) <= 1)

    def _c_no_cohort_clash(self) -> None:
        cohort_acts: Dict[str, List[str]] = {}
        for a in self.data.activities:
            if a.get("duration_periods", 0) == 0:
                continue
            cohort_acts.setdefault(a["cohort_id"], []).append(a["id"])
            joint = a.get("joint_cohort_ids") or ""
            for jc in [x.strip() for x in joint.split(",") if x.strip()]:
                cohort_acts.setdefault(jc, []).append(a["id"])
        for cohort_id, act_ids in cohort_acts.items():
            unique_acts = list(set(act_ids))
            for p in self.data.periods:
                vars_here = [v for (aid, pid, _), v in self.x.items() if aid in unique_acts and pid == p["id"]]
                if len(vars_here) > 1:
                    self.model.Add(sum(vars_here) <= 1)

    def _c_one_exam_per_day(self) -> None:
        cohort_acts: Dict[str, List[str]] = {}
        for a in self.data.activities:
            if a.get("duration_periods", 0) == 0:
                continue
            cohort_acts.setdefault(a["cohort_id"], []).append(a["id"])
        for cohort_id, act_ids in cohort_acts.items():
            for day in set(p["day"] for p in self.data.periods):
                day_period_ids = [p["id"] for p in self.data.periods if p["day"] == day]
                vars_today = [v for (aid, pid, _), v in self.x.items() if aid in act_ids and pid in day_period_ids]
                if len(vars_today) > 1:
                    self.model.Add(sum(vars_today) <= 1)

    def _c_capacity(self) -> None:
        for a in self.data.activities:
            aid = a["id"]
            if a.get("duration_periods", 0) == 0:
                continue
            for p in self.data.periods:
                for r in self.data.rooms:
                    if r["capacity"] < a.get("students", 0):
                        key = (aid, p["id"], r["code"])
                        if key in self.x:
                            self.model.Add(self.x[key] == 0)

    def _c_breaks_excluded(self) -> None:
        for p in self.data.periods:
            if not p["is_break"]:
                continue
            for (_, pid, _), v in self.x.items():
                if pid == p["id"]:
                    self.model.Add(v == 0)

    def _c_lab_rooms(self) -> None:
        for a in self.data.activities:
            aid = a["id"]
            if a.get("duration_periods", 0) == 0:
                continue
            pref = a.get("preferred_room_type", "Lecture")
            if pref not in ("Science Lab", "Clinical Lab", "Computer Lab"):
                continue
            for p in self.data.periods:
                for r in self.data.rooms:
                    if r["room_type"] != pref:
                        key = (aid, p["id"], r["code"])
                        if key in self.x:
                            self.model.Add(self.x[key] == 0)

    # ------------------------------------------------------------
    # Soft constraints
    # ------------------------------------------------------------
    def _add_soft_constraints(self) -> None:
        penalties = []
        if self.run_type == "teaching":
            penalties += self._s_preferred_room_type()
            penalties += self._s_lecturer_preferred_mode()
            penalties += self._s_avoid_long_blocks()
            penalties += self._s_friday_computer_skills()
            penalties += self._s_lecturer_gaps()
            penalties += self._s_spread_modules()
        elif self.run_type in ("test", "exam"):
            penalties += self._s_exam_morning()
            penalties += self._s_avoid_saturday()
        if penalties:
            self.model.Minimize(sum(penalties))

    def _s_preferred_room_type(self) -> List:
        penalties = []
        for a in self.data.activities:
            aid = a["id"]
            if a.get("duration_periods", 0) == 0:
                continue
            pref = a.get("preferred_room_type", "Lecture")
            for p in self.data.periods:
                for r in self.data.rooms:
                    key = (aid, p["id"], r["code"])
                    if key in self.x and r["room_type"] != pref:
                        penalties.append(self.x[key])
        return penalties

    def _s_lecturer_preferred_mode(self) -> List:
        penalties = []
        for a in self.data.activities:
            aid = a["id"]
            if a.get("duration_periods", 0) == 0:
                continue
            lect = next((l for l in self.data.lecturers if l["id"] == a["lecturer_id"]), None)
            if not lect:
                continue
            pref = lect.get("preferred_mode", "Both")
            if pref == "Both":
                continue
            for p in self.data.periods:
                if p["mode"] != pref:
                    for r in self.data.rooms:
                        key = (aid, p["id"], r["code"])
                        if key in self.x:
                            penalties.append(self.x[key])
        return penalties

    def _s_avoid_long_blocks(self) -> List:
        penalties = []
        cohort_acts: Dict[str, List[str]] = {}
        for a in self.data.activities:
            if a.get("duration_periods", 0) == 0:
                continue
            cohort_acts.setdefault(a["cohort_id"], []).append(a["id"])
        for cohort_id, act_ids in cohort_acts.items():
            if len(act_ids) < 3:
                continue
            for day in set(p["day"] for p in self.data.periods):
                day_periods = [p for p in self.data.periods if p["day"] == day and not p["is_break"]]
                for i in range(len(day_periods) - 2):
                    p1, p2, p3 = day_periods[i], day_periods[i+1], day_periods[i+2]
                    vars1 = [v for (aid, pid, _), v in self.x.items() if aid in act_ids and pid == p1["id"]]
                    vars2 = [v for (aid, pid, _), v in self.x.items() if aid in act_ids and pid == p2["id"]]
                    vars3 = [v for (aid, pid, _), v in self.x.items() if aid in act_ids and pid == p3["id"]]
                    if not (vars1 and vars2 and vars3):
                        continue
                    block = self.model.NewBoolVar("block_" + str(cohort_id) + "_" + str(p1["id"]))
                    self.model.Add(sum(vars1) + sum(vars2) + sum(vars3) <= 2 + block)
                    self.model.Add(sum(vars1) >= block)
                    self.model.Add(sum(vars2) >= block)
                    self.model.Add(sum(vars3) >= block)
                    penalties.append(block)
        return penalties

    def _s_friday_computer_skills(self) -> List:
        penalties = []
        for a in self.data.activities:
            aid = a["id"]
            if a.get("duration_periods", 0) == 0:
                continue
            mod = a.get("module_code", "")
            if "IT 51102" not in mod:
                continue
            for p in self.data.periods:
                is_preferred = (p["day"] == "Friday" and p["start_time"] == "11:00")
                if is_preferred:
                    continue
                for r in self.data.rooms:
                    key = (aid, p["id"], r["code"])
                    if key in self.x:
                        penalties.append(self.x[key])
        return penalties

    # ------------------------------------------------------------
    # C009 -- keep lecturer gaps low
    # ------------------------------------------------------------
    def _s_lecturer_gaps(self) -> List:
        """For each lecturer, penalize days where they have isolated periods (gaps).

        We use a simpler proxy: penalize situations where a lecturer teaches
        on a day but has a big hole between their first and last class.
        Implementation: penalize each teaching session on a day at a period
        that is far from other sessions on the same day.
        """
        penalties = []
        lect_acts: Dict[str, List[str]] = {}
        for a in self.data.activities:
            if a.get("duration_periods", 0) == 0:
                continue
            lect_acts.setdefault(a["lecturer_id"], []).append(a["id"])

        for lect_id, act_ids in lect_acts.items():
            if len(act_ids) < 2:
                continue  # No gaps possible with 1 activity
            for day in set(p["day"] for p in self.data.periods):
                day_periods = sorted(
                    [p for p in self.data.periods if p["day"] == day and not p["is_break"]],
                    key=lambda x: x["order_index"]
                )
                if len(day_periods) < 3:
                    continue
                # For each triple (p1, p2, p3), penalize if p2 is a gap:
                # lecturer teaches at p1 AND p3 but not p2 -> penalty
                for i in range(len(day_periods) - 2):
                    p1 = day_periods[i]
                    p2 = day_periods[i+1]
                    p3 = day_periods[i+2]
                    vars1 = [v for (aid, pid, _), v in self.x.items() if aid in act_ids and pid == p1["id"]]
                    vars3 = [v for (aid, pid, _), v in self.x.items() if aid in act_ids and pid == p3["id"]]
                    vars2 = [v for (aid, pid, _), v in self.x.items() if aid in act_ids and pid == p2["id"]]
                    if not (vars1 and vars2 and vars3):
                        continue
                    has1 = self.model.NewBoolVar("lg_has1_" + str(lect_id) + "_" + str(p1["id"]))
                    has2 = self.model.NewBoolVar("lg_has2_" + str(lect_id) + "_" + str(p2["id"]))
                    has3 = self.model.NewBoolVar("lg_has3_" + str(lect_id) + "_" + str(p3["id"]))
                    self.model.Add(sum(vars1) >= has1)
                    self.model.Add(sum(vars1) <= 100 * has1)
                    self.model.Add(sum(vars2) >= has2)
                    self.model.Add(sum(vars2) <= 100 * has2)
                    self.model.Add(sum(vars3) >= has3)
                    self.model.Add(sum(vars3) <= 100 * has3)

                    # gap = has1 AND (NOT has2) AND has3
                    gap = self.model.NewBoolVar("gap_" + str(lect_id) + "_" + str(p2["id"]))
                    self.model.Add(gap <= has1)
                    self.model.Add(gap <= has3)
                    self.model.Add(gap <= (1 - has2))
                    self.model.Add(gap >= has1 + has3 - has2 - 1)
                    penalties.append(gap)
        return penalties

    # ------------------------------------------------------------
    # C011 -- spread modules across the week
    # ------------------------------------------------------------
    def _s_spread_modules(self) -> List:
        """Penalize scheduling the same module twice on the same day for a cohort.

        Groups activities by (cohort_id, module_code). For each pair that
        appears on the same day, add a penalty.
        """
        penalties = []
        # Group by (cohort_id, module_code)
        groups: Dict[Tuple[str, str], List[str]] = {}
        for a in self.data.activities:
            if a.get("duration_periods", 0) == 0:
                continue
            key = (a["cohort_id"], a["module_code"])
            groups.setdefault(key, []).append(a["id"])

        for (cohort_id, module_code), act_ids in groups.items():
            if len(act_ids) < 2:
                continue  # nothing to spread
            for day in set(p["day"] for p in self.data.periods):
                day_period_ids = [p["id"] for p in self.data.periods if p["day"] == day and not p["is_break"]]
                # Count how many of these activities are on the same day
                vars_today = [
                    v for (aid, pid, _), v in self.x.items()
                    if aid in act_ids and pid in day_period_ids
                ]
                if len(vars_today) < 2:
                    continue
                # Penalize if 2+ of the same module are on the same day
                same_day = self.model.NewBoolVar(
                    "same_day_" + str(hash((cohort_id, module_code, day)) & 0xFFFF)
                )
                self.model.Add(sum(vars_today) <= 1 + 10 * same_day)
                self.model.Add(sum(vars_today) >= 2 * same_day)
                penalties.append(same_day)
        return penalties

    def _s_exam_morning(self) -> List:
        penalties = []
        for a in self.data.activities:
            aid = a["id"]
            if a.get("duration_periods", 0) == 0:
                continue
            for p in self.data.periods:
                if p["start_time"] not in ("08:00", "10:30", "09:00"):
                    for r in self.data.rooms:
                        key = (aid, p["id"], r["code"])
                        if key in self.x:
                            penalties.append(self.x[key])
        return penalties

    def _s_avoid_saturday(self) -> List:
        penalties = []
        for a in self.data.activities:
            aid = a["id"]
            if a.get("duration_periods", 0) == 0:
                continue
            for p in self.data.periods:
                if p["day"] != "Saturday":
                    continue
                for r in self.data.rooms:
                    key = (aid, p["id"], r["code"])
                    if key in self.x:
                        penalties.append(self.x[key] * 2)
        return penalties

    # ------------------------------------------------------------
    # Solve
    # ------------------------------------------------------------
    def solve(self, time_limit: Optional[int] = None, num_workers: Optional[int] = None, seed: Optional[int] = None) -> SolverOutput:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit or settings.SOLVER_TIME_LIMIT_SECONDS
        solver.parameters.num_search_workers = num_workers or settings.SOLVER_NUM_WORKERS
        solver.parameters.random_seed = seed if seed is not None else settings.SOLVER_RANDOM_SEED

        logger.info(f"Running CP-SAT solver (run_type={self.run_type})...")
        status = solver.Solve(self.model)

        assignments: List[dict] = []
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for (aid, pid, rcode), var in self.x.items():
                if solver.Value(var) == 1:
                    assignments.append({
                        "activity_id": aid,
                        "period_id": pid,
                        "room_code": rcode,
                        "split_group": 0,
                    })

        status_name = {
            cp_model.OPTIMAL: "optimal",
            cp_model.FEASIBLE: "feasible",
            cp_model.INFEASIBLE: "infeasible",
            cp_model.MODEL_INVALID: "invalid",
            cp_model.UNKNOWN: "unknown",
        }.get(status, "unknown")

        return SolverOutput(
            status=status_name,
            assignments=assignments,
            objective_value=solver.ObjectiveValue() if status in (cp_model.OPTIMAL, cp_model.FEASIBLE) else 0.0,
            wall_time=solver.WallTime(),
            message=f"Solver status: {status_name}",
        )