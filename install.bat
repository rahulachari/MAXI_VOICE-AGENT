@echo off
title JARVIS VoiceOS - Permanent Installer
cd /d "%~dp0"
echo =======================================================
echo    Installing JARVIS VoiceOS permanently...
echo =======================================================
python installer\install_service.py
echo.
pause
