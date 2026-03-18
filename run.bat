@echo off
REM WebGuard RF - Start backend and frontend
echo Starting WebGuard RF...
echo.
echo Backend: http://localhost:8001
echo Frontend: http://localhost:3000 (or 3001 if 3000 in use)
echo.
start "WebGuard Backend" cmd /k "cd /d "%~dp0" && python run_backend.py"
timeout /t 3 /nobreak >nul
start "WebGuard Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"
echo.
echo Both servers started. Close the terminal windows to stop.
