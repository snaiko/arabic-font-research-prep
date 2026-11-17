@echo off
setlocal
cd /d "%~dp0"
echo ===============================================
echo Arabic Font Research - Local AI Agent Preflight
echo ===============================================
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 scripts\preflight_local_training.py
) else (
  python scripts\preflight_local_training.py
)
echo.
echo Preflight finished. No training was started.
echo Read LOCAL_AI_AGENT_GUIDE.md and reports\local\machine_preflight.json
pause
