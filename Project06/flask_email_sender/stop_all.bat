@echo off
echo Stopping Flask, Celery, and Redis...

taskkill /IM python.exe /F
taskkill /IM redis-server.exe /F
taskkill /IM celery.exe /F

echo All services stopped.
exit
