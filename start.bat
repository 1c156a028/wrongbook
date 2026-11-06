@echo off
rem ===========================================================
rem  WrongBook - one click launcher
rem  Starts the local dev server and opens it in the browser.
rem  Close this window or press Ctrl+C to stop the server.
rem ===========================================================
setlocal
title WrongBook
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo  [!] Virtual environment not found.
    echo      Run these two commands first:
    echo.
    echo        python -m venv .venv
    echo        .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

if not exist "wrongbook.db" (
    echo [i] Database not found, creating it with demo data...
    ".venv\Scripts\python.exe" seed.py
    echo.
)

rem Open the browser 3 seconds later, once the server is listening.
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:5000'"

echo.
echo   WrongBook  ->  http://127.0.0.1:5000
echo   Press Ctrl+C to stop the server.
echo.

".venv\Scripts\python.exe" app.py

echo.
echo Server stopped.
pause
