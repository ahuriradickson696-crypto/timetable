# AVIU Timetable System - User Manual

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
