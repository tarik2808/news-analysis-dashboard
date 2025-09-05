@echo off
cd /d "C:\Users\DT User\Desktop\SDP Project"
call venv310\Scripts\activate.bat
python weekly_newsletter_scheduler.py
pause 