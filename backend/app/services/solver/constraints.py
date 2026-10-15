"""Constraint definitions for the AVIU timetable solver.

Maps C001-C018 from the AVIU Master Data Workbook (sheet 08_Constraints).
"""
from dataclasses import dataclass
from typing import List


@dataclass
class ConstraintSpec:
    id: str
    type: str
    category: str
    description: str
    weight: int


AVIU_CONSTRAINTS: List[ConstraintSpec] = [
    ConstraintSpec("C001", "Hard", "Teacher", "No lecturer double-booking", 100),
    ConstraintSpec("C002", "Hard", "Room", "No room double-booking", 100),
    ConstraintSpec("C003", "Hard", "Student", "No cohort double-booking", 100),
    ConstraintSpec("C004", "Hard", "Room", "Students fit in room capacity", 100),
    ConstraintSpec("C005", "Hard", "Time", "Mode separation (Day vs Weekend)", 100),
    ConstraintSpec("C006", "Hard", "Teacher", "Respect lecturer max hours/week", 100),
    ConstraintSpec("C007", "Soft", "Teacher", "Prefer lecturer Preferred_Mode", 80),
    ConstraintSpec("C008", "Soft", "Student", "Avoid >2 consecutive periods without break", 70),
    ConstraintSpec("C009", "Soft", "Teacher", "Keep lecturer gaps low", 60),
    ConstraintSpec("C010", "Soft", "Room", "Prefer Preferred_Room_Type", 50),
    ConstraintSpec("C011", "Soft", "Student", "Spread modules across the week", 40),
    ConstraintSpec("C012", "Hard", "Time", "No teaching in break periods", 100),
    ConstraintSpec("C013", "Hard", "Time", "No weekend teaching this semester", 100),
    ConstraintSpec("C014", "Hard", "Time", "Joint activities at same time", 100),
    ConstraintSpec("C015", "Hard", "Time", "Sessions never exceed 2 consecutive periods", 100),
    ConstraintSpec("C016", "Hard", "Room", "Lab activities only in matching rooms", 100),
    ConstraintSpec("C017", "Soft", "Teacher", "Keep Basic Computer Skills on Fri 11-13", 90),
    ConstraintSpec("C018", "Hard", "Time", "Skip 0-contact-hour off-campus units", 100),
]


def hard_constraints() -> List[ConstraintSpec]:
    return [c for c in AVIU_CONSTRAINTS if c.type == "Hard"]


def soft_constraints() -> List[ConstraintSpec]:
    return [c for c in AVIU_CONSTRAINTS if c.type == "Soft"]
