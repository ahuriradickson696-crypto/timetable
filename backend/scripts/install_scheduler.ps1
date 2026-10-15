# Register a Windows Scheduled Task to run the pipeline nightly
$taskName = "AVIU-Timetable-Nightly-Sync"
$backendPath = "C:\Users\MAS GLOBAL TECH\aviu-timetable\backend"
$pythonExe = "$backendPath\venv\Scripts\python.exe"
$scriptPath = "$backendPath\scripts\scheduled_sync.py"

Write-Host "Registering scheduled task: $taskName" -ForegroundColor Cyan

# Remove existing task if any
schtasks /Query /TN "$taskName" 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Removing old task..." -ForegroundColor Yellow
    schtasks /Delete /TN "$taskName" /F | Out-Null
}

# Create new task: run every day at 2:00 AM
$action = "`"$pythonExe`" `"$scriptPath`""
schtasks /Create /TN "$taskName" /TR "$action" /SC DAILY /ST 02:00 /RL HIGHEST /F | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "OK Scheduled task created. Runs daily at 2:00 AM." -ForegroundColor Green
    Write-Host "   View with: schtasks /Query /TN `"$taskName`" /V /FO LIST" -ForegroundColor Gray
} else {
    Write-Host "Failed to create task. Run PowerShell as Administrator." -ForegroundColor Red
}

Write-Host ""
Write-Host "Other options:" -ForegroundColor Cyan
Write-Host "  Remove task:  schtasks /Delete /TN `"$taskName`" /F" -ForegroundColor Gray
Write-Host "  Run now:      schtasks /Run /TN `"$taskName`"" -ForegroundColor Gray