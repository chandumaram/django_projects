@echo off
title Starting Redis, Celery, and Flask
cd /d "C:\My Data\Python Practice\django_projects\Project06\flask_email_sender"

echo Starting Redis Server...
start cmd /k "redis-server"

timeout /t 5

echo Activating Virtual Environment...
call venv\Scripts\activate

echo Starting Celery Worker...
start cmd /k "celery -A celery_worker worker --loglevel=info --pool=threads"

timeout /t 5

echo Starting Flask App...
start cmd /k "python app.py"

echo All services started successfully!
exit
