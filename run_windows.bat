@echo off
setlocal

:: Title in English
title HOI4 Web Translator - Running...
color 0A

echo.
echo  ==============================================
echo     Starting HOI4 Web Translator...
echo  ==============================================
echo.

:: Try to use venv python directly
if exist "backend\venv\Scripts\python.exe" (
    echo  [1] Found Virtual Environment. Using venv python.
    "backend\venv\Scripts\python.exe" start.py
) else (
    echo  [WARNING] venv not found. Using system python.
    python start.py
)

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start server.
    echo If 'uvicorn' module is missing, please run setup_windows.bat first.
    pause
)
