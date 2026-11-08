@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
 echo Không tìm thấy trình khởi chạy Python. Hãy cài Python 3.12 từ python.org.
 echo Nhấn phím bất kỳ để tiếp tục.
pause >nul
 exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
 py -3.12 -m venv .venv
 if errorlevel 1 (
  echo Không tạo được môi trường ảo. Hãy kiểm tra Python 3.12 đã được cài đặt.
  echo Nhấn phím bất kỳ để tiếp tục.
pause >nul
  exit /b 1
 )
)
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -e ".[gui,dev]"
if errorlevel 1 (
 echo Cài đặt thư viện thất bại. Hãy kiểm tra kết nối mạng và lỗi ở trên.
 echo Nhấn phím bất kỳ để tiếp tục.
pause >nul
 exit /b 1
)
echo.
echo Đã cài đặt. Nhấp đúp run_windows.bat để mở bảng điều khiển.
echo Nhấn phím bất kỳ để tiếp tục.
pause >nul
