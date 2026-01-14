@echo off
setlocal

:: English Only to prevent encoding issues
echo Checking Python installation...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from python.org
    echo Don't forget to check "Add Python to PATH" during installation.
    pause
    exit /b
)

:: Run the Python installer script
python install.py

if %errorlevel% neq 0 (
    echo.
    echo Installation failed.
    pause
)
