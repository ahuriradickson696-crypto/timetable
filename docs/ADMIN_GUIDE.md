# AVIU Timetable - Administrator Guide

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
