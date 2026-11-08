@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Please run: py -3.12 -m venv .venv
 echo Then run: .venv\Scripts\python.exe -m pip install -e ".[gui,dev]"
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -m mechavision gui
if errorlevel 1 pause
