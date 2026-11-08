@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
 echo Python launcher not found. Install Python 3.12 from python.org first.
 pause
 exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
 py -3.12 -m venv .venv
 if errorlevel 1 (
  echo Could not create virtual environment. Make sure Python 3.12 is installed.
  pause
  exit /b 1
 )
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -e ".[gui,dev]"
if errorlevel 1 (
 echo Dependency installation failed. Check network and errors above.
 pause
 exit /b 1
)
echo.
echo Installed. Double-click run_windows.bat to open the dashboard.
pause
