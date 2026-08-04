@echo off
REM ==== Bot02 Starter ====
REM Aktiviert die virtuelle Umgebung und startet einen Lauf.
REM Wird auch vom Windows Task Scheduler alle 5 Stunden aufgerufen.
cd /d C:\Bot02
call .venv\Scripts\activate.bat
python src\run.py >> logs\run.log 2>&1
