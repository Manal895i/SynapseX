@echo off
title ADEIP — Dev Server
echo.
echo  ================================================
echo   ADEIP — Autonomous Digital Evidence Intel Platform
echo  ================================================
echo.

:: Start Backend
echo  [1/2] Starting Backend (FastAPI + Uvicorn)...
cd /d "%~dp0backend"
start cmd /k "title ADEIP Backend && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

:: Start Frontend
echo  [2/2] Starting Frontend (React + Vite)...
cd /d "%~dp0frontend"
start cmd /k "title ADEIP Frontend && npm run dev"

:: Wait a moment then open browser
timeout /t 4 /nobreak >nul
start http://localhost:5173

echo.
echo  Backend running at:  http://127.0.0.1:8000
echo  API Documentation:   http://127.0.0.1:8000/docs
echo  Frontend running at: http://localhost:5173
echo.
echo  Close the terminal windows to stop the servers.
echo.
pause
