@echo off
title JARVIS VoiceOS - Uninstaller
cd /d "%~dp0"
echo =======================================================
echo    Uninstalling JARVIS VoiceOS Startup Shortcuts...
echo =======================================================
python installer\install_service.py uninstall
echo.
pause
