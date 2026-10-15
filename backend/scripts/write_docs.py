import os

root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
docs_dir = os.path.join(root, "docs")
os.makedirs(docs_dir, exist_ok=True)

USER_MANUAL = """# AVIU Timetable System - User Manual

**Avance International University** - Automated timetabling system

Version 1.0 - October 2026

## 1. Overview

The AVIU Timetable System automates university scheduling. It replaces
manual Excel/Word planning with a clash-free, constraint-based solver
that runs in seconds.

What it does:
- Reads your Excel curriculum workbook
- Auto-generates teaching activities, tests, and final exams
- Assigns qualified lecturers automatically
- Solves clash-free timetables using OR-Tools
- Publishes to students and lecturers
- Exports PDF, Excel, and iCal

## 2. Logging In

URL: http://localhost:5173 (dev) or https://timetable.avance.ac.ug (prod)

Default credentials:
- Admin: admin@aviu.ac.ug / admin123
- Student: student1@aviu.ac.ug / student123
- Lecturer: lecturer1@aviu.ac.ug / lecturer123

Change the default password immediately after first login.

## 3. Roles and Access

Admin      : Everything
Officer    : CRUD + generate + publish
Viewer     : Read-only admin views
Student    : See own timetable
Lecturer   : See own schedule

## 4. Automatic Workflow

Option A - Drag and Drop:
1. Log in as admin
2. Click "Import Data" in the sidebar
3. Drag the Excel workbook into the drop zone
4. Optionally check "Auto-publish"
5. Click "Upload & Run Pipeline"

The system imports master data, generates activities, assigns lecturers,
runs the solver, publishes (if requested), and archives the previous file.

Option B - Folder Watcher:
Run `py scripts/watch.py` in backend/. Any .xlsx dropped into data/
triggers the pipeline automatically.

Option C - Nightly Scheduled Run:
Windows Task: AVIU-Timetable-Nightly-Sync, daily at 2:00 AM.

## 5. Excel Workbook Format

Required sheets:
- 01_Programmes
- 02_Cohorts
- 03_Course_Units
- 04_Lecturers
- 05_Rooms
- 06_Time_Structure

Optional:
- 07_Activities (auto-generated if empty)

Module Code Format: PROG UNIT [LEVEL][YEAR][SEM][ORDER]
Example: BSE ED 71101 = BSE + Education + Level 7 + Year 1 + Sem 1 + Order 01

## 6. Generating Timetables

Via UI:
1. Sidebar -> Generate
2. Choose type: Teaching / Test / Final Exam
3. Set intake, academic year, semester
4. Click "Run Solver"

View Timetable:
1. Sidebar -> View Timetable
2. Pick a run from dropdown
3. Choose view: By Cohort / By Lecturer / By Room

Manual adjustments: drag any cell to move it.

## 7. Publishing

Click "Publish" on the Timetable view. Only one published run per
(intake, year, semester, type). Publishing auto-unpublishes the previous.

To fix: click Unlock, edit, re-publish.

## 8. Analytics

Room Utilisation heatmap, Lecturer Load report, Programme Summary cards,
Cohort Weekly Load heatmap.

## 9. Student and Lecturer Portals

Students see their own cohort timetable. Lecturers see their own schedule.
Both can export to iCal.

## 10. Creating Users

Sidebar -> Users. Fill in email, name, password, role. Link students to
cohorts and lecturers to lecturer IDs.

## 11. Backup and Recovery

Data lives in:
- backend/aviu_timetable.db (database)
- data/uploads/current.xlsx (current workbook)
- data/uploads/archive/ (previous versions)

Backup the DB: Copy-Item backend/aviu_timetable.db backup.db
Restore previous workbook: Import Data page -> click Restore.

## 12. Troubleshooting

Failed to fetch          : Backend not running
Solver infeasible        : Too many activities; reduce hours
Port already in use      : Another instance is running
Blank page               : Press F12 and check console
Module code not parsed   : Check format PROG UNIT [LEVEL][YEAR][SEM][NN]

## 13. Support

Contact the ICT Department.

End of User Manual.
"""


ADMIN_GUIDE = """# AVIU Timetable - Administrator Guide

For the ICT Department maintaining the system.

## Daily Operations

Start:   cd C:/Users/MAS GLOBAL TECH/aviu-timetable ; ./start.ps1
Stop:    ./stop.ps1
Status:  ./status.ps1

Start folder watcher:
    cd backend
    ./venv/Scripts/Activate.ps1
    py scripts/watch.py

Restart backend:
    cd backend
    ./venv/Scripts/Activate.ps1
    py -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

Restart frontend:
    cd frontend
    npm run dev

## Database Operations

Reset database (danger):
    cd backend
    ./venv/Scripts/Activate.ps1
    Remove-Item aviu_timetable.db -Force
    py -m app.seed
    py scripts/run_import.py
    py scripts/seed_exam_periods.py

Backup:
    Copy-Item backend/aviu_timetable.db backups/backup.db

## API Access

Docs:    http://localhost:8000/docs
OpenAPI: http://localhost:8000/openapi.json

## Diagnostics

Backend health:
    Invoke-RestMethod http://localhost:8000/health

Run tests:
    cd backend
    ./venv/Scripts/Activate.ps1
    py -m pytest tests/ -v

## Scheduled Tasks

View:     Get-ScheduledTask -TaskName "AVIU-Timetable-Nightly-Sync"
Run now:  Start-ScheduledTask -TaskName "AVIU-Timetable-Nightly-Sync"
Disable:  Disable-ScheduledTask -TaskName "AVIU-Timetable-Nightly-Sync"
Remove:   Unregister-ScheduledTask -TaskName "AVIU-Timetable-Nightly-Sync" -Confirm:$false

## Common Tasks

Add a new programme: edit Excel 01_Programmes, save, upload.

Fix a clash: View Timetable -> Unlock -> drag -> Publish.

Reset admin password:
    cd backend
    ./venv/Scripts/Activate.ps1
    py -c "from app.db.session import SessionLocal; from app.models.user import User; from app.core.security import hash_password; db = SessionLocal(); u = db.query(User).filter_by(email='admin@aviu.ac.ug').first(); u.hashed_password = hash_password('newpassword'); db.commit(); db.close()"

End of Admin Guide.
"""


README = """# AVIU Timetabling System

Avance International University - Automated, clash-free timetabling.

## Quick Start

Backend:
    cd backend
    python -m venv venv
    ./venv/Scripts/Activate.ps1
    pip install -r requirements.txt
    python -m app.seed
    python scripts/run_import.py
    python scripts/seed_exam_periods.py
    uvicorn app.main:app --reload

Frontend (new terminal):
    cd frontend
    npm install
    npm run dev

Open http://localhost:5173
Login: admin@aviu.ac.ug / admin123

## Automatic Workflow

1. Edit the Excel workbook
2. Drop it in the browser (Import Data page) or the data/ folder
3. System imports, generates activities, assigns lecturers, solves,
   and optionally publishes - all automatically.

## Stack

- Backend: FastAPI + SQLAlchemy + Pydantic
- Solver: Google OR-Tools CP-SAT
- Database: SQLite (dev) / PostgreSQL (production)
- Frontend: React 18 + TypeScript + Vite + Tailwind
- Auth: JWT + bcrypt

## Features

- Drag-drop Excel upload with full pipeline
- Folder watcher
- Auto-generate activities from curriculum
- Auto-assign qualified lecturers
- Clash-free timetabling (18 constraints)
- Teaching, tests, final exam schedules
- Publish/lock workflow
- Analytics with heatmaps
- Student and lecturer portals
- iCal / PDF / Excel export
- Search, sort, paginate on all tables
- Drag-drop manual adjustments
- Full audit trail
- Archive + rollback
- Nightly scheduled runs

## Tests

    cd backend
    ./venv/Scripts/Activate.ps1
    python -m pytest tests/ -v

## License

Internal use only - Avance International University
"""


# Write without BOM
with open(os.path.join(docs_dir, "USER_MANUAL.md"), "w", encoding="utf-8") as fh:
    fh.write(USER_MANUAL)

with open(os.path.join(docs_dir, "ADMIN_GUIDE.md"), "w", encoding="utf-8") as fh:
    fh.write(ADMIN_GUIDE)

with open(os.path.join(root, "README.md"), "w", encoding="utf-8") as fh:
    fh.write(README)

print("OK docs/USER_MANUAL.md written (" + str(len(USER_MANUAL)) + " chars)")
print("OK docs/ADMIN_GUIDE.md written (" + str(len(ADMIN_GUIDE)) + " chars)")
print("OK README.md written (" + str(len(README)) + " chars)")
