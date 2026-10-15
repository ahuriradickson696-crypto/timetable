# AVIU Timetabling System

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
