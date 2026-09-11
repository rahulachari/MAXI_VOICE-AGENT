@echo off
title VoiceOS Launcher
cd /d "%~dp0"
echo Starting VoiceOS Floating Notch...
start "" "%~dp0VoiceOS.exe"
echo VoiceOS is now running in the background!
echo Press and hold [Ctrl] + [Alt] to talk.
timeout /t 3
