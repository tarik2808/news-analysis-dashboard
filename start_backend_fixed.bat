@echo off
echo Starting Backend Server (Windows Fixed Version)...
cd /d "C:\Users\DT User\Desktop\SDP Project"
call venv310\Scripts\activate.bat
echo Backend starting on http://localhost:8000
echo Keep this window open!
python start_backend_windows_fixed.py
pause
