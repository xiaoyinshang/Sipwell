@echo off
setlocal

set "TASK_NAME=SipwellHourlyReminder"

schtasks /delete /tn "%TASK_NAME%" /f
if errorlevel 1 (
  echo [WARN] Task may not exist: %TASK_NAME%
  pause
  exit /b 1
)

echo [OK] Startup task removed: %TASK_NAME%
pause
