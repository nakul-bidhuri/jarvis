@echo off
title J.A.R.V.I.S Auto-Start Installer
echo Installing J.A.R.V.I.S silent background auto-start on Windows boot...

set "SCRIPT_DIR=%~dp0"
set "VBS_TARGET=%SCRIPT_DIR%start_jarvis.vbs"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_DIR%\JarvisAssistant.lnk"

if not exist "%VBS_TARGET%" (
    echo [ERROR] Could not find start_jarvis.vbs in %SCRIPT_DIR%
    pause
    exit /b 1
)

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT_PATH%'); $s.TargetPath = '%VBS_TARGET%'; $s.WorkingDirectory = '%SCRIPT_DIR%'; $s.WindowStyle = 7; $s.Save()"

echo.
echo [SUCCESS] J.A.R.V.I.S will now start automatically in silent standby mode whenever your laptop boots!
echo Ignition: Say "Hey Jarvis" or press Ctrl+Alt+J
echo Standby:  Say "Goodbye Jarvis" or "Jarvis jao"
pause
