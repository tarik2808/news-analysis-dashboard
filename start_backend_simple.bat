@echo off
echo Starting Backend Server...
cd /d "C:\Users\DT User\Desktop\SDP Project"
call venv310\Scripts\activate.bat
echo Backend starting on http://localhost:8000
echo Keep this window open!
python -c "import uvicorn; from api import app; uvicorn.run(app, host='127.0.0.1', port=8000, log_level='info')"
pause
