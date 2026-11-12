@echo off
echo Stopping any running Jarvis instances...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Jarvis*" >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
echo Done! All Jarvis instances have been stopped.
pause
