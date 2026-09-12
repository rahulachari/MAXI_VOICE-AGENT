@echo off
title JARVIS VoiceOS Launcher
cd /d "%~dp0"
echo ========================================================
echo       Starting JARVIS VoiceOS Floating Dynamic Island
echo ========================================================
echo.
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*run.py*' -and $_.ProcessId -ne $PID } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" 2>nul
start "" pythonw run.py
echo [OK] JARVIS VoiceOS is active!
echo [OK] Floating Dynamic Island is at the top of your screen.
echo [OK] Press and hold [Ctrl] + [Alt] to speak.
echo.
timeout /t 3 >nul
