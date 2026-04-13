@echo off
setlocal

set "EXE_PATH=E:\xproject\20260413_Sipwell_v1\dist\sipwell.exe"
set "TASK_NAME=SipwellHourlyReminder"

if not exist "%EXE_PATH%" (
  echo [ERROR] EXE not found: %EXE_PATH%
  pause
  exit /b 1
)

schtasks /create /tn "%TASK_NAME%" /tr "\"%EXE_PATH%\"" /sc onlogon /rl limited /f
if errorlevel 1 (
  echo [ERROR] Failed to create startup task.
  pause
  exit /b 1
)

echo [OK] Startup task created: %TASK_NAME%
echo It will run when user logs on.
pause
