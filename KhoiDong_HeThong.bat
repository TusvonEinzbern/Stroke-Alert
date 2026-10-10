@echo off
title He Thong Phat Hien Dot Quy
color 0B
echo ===================================================
echo     HE THONG PHAN TICH CHUYEN DONG VA DOT QUY
echo ===================================================
echo.
echo Dang khoi dong cac module AI (MediaPipe)...
echo Vui long cho trong vai giay...

:: Chuyển thư mục hiện tại về thư mục chứa file bat
cd /d "%~dp0"

:: Đặt mã hóa UTF-8 để tránh lỗi hiển thị tiếng Việt
set PYTHONIOENCODING=utf-8

:: Chạy Desktop App bằng PyWebView
echo Dang khoi dong Giao dien Desktop (UI)...
.\.venv\Scripts\python.exe webview_app.py

echo.
echo [!] Chuong trinh da dung lai hoac xay ra loi.
pause
