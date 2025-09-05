@echo off
cd /d "C:\Users\DT User\Desktop\SDP Project"
call venv310\Scripts\activate.bat
python -m uvicorn api:app --host 0.0.0.0 --port 8000
pause
