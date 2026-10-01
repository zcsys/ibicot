@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
  py -3 serve.py
) else (
  where python >nul 2>nul
  if not errorlevel 1 (
    python serve.py
  ) else (
    echo Python 3 is required to start the simulator.
    echo Install it from https://www.python.org/downloads/
    pause
    exit /b 1
  )
)

if errorlevel 1 (
  echo.
  echo Startup failed.
  pause
)
