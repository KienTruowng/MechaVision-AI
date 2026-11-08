@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Hãy chạy: py -3.12 -m venv .venv
 echo Sau đó chạy: .venv\Scripts\python.exe -m pip install -e ".[gui,dev]"
 echo Nhấn phím bất kỳ để tiếp tục.
 pause >nul
 exit /b 1
)
".venv\Scripts\python.exe" -m mechavision gui
if errorlevel 1 (
 echo Nhấn phím bất kỳ để tiếp tục.
 pause >nul
)
