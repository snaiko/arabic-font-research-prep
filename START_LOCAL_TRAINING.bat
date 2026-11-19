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
if errorlevel 1 (
  echo Preflight is BLOCKED. Read blocking_reasons in reports\local\machine_preflight.json.
) else (
  echo Preflight PASSED for the experimental image-reference raster route.
)
echo No training was started.
echo Read reports\local\machine_preflight.json
pause
