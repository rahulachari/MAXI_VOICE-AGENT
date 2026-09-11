@echo off
echo Building JARVIS VoiceOS Application...
echo.

echo [1/2] Compiling Python executable with PyInstaller...
pyinstaller --clean -y jarvis.spec
if %ERRORLEVEL% neq 0 (
    echo [ERROR] PyInstaller build failed.
    exit /b %ERRORLEVEL%
)

echo.
echo [2/2] Generating JARVIS-Setup.exe installer with Inno Setup...
echo Make sure you have Inno Setup installed (https://jrsoftware.org/isinfo.php)
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" setup.iss
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Inno Setup compilation failed.
    echo Please make sure Inno Setup is installed and in the default directory.
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================================
echo Build Complete! 
echo Installer is located at: installer\dist\JARVIS-Setup.exe
echo ========================================================
pause
