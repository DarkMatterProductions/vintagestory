@echo off
REM Startup script for Vintage Story RCon Web Client (Windows)

echo Starting Vintage Story RCon Web Client...
echo.

REM Change to the script's directory
cd /d "%~dp0"

REM Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Start the application
echo.
echo Starting server...
echo.
python app.py

pause

