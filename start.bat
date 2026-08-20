@echo off
title ADEIP — Dev Server
echo.
echo  ================================================
echo   ADEIP — Autonomous Digital Evidence Intel Platform
echo  ================================================
echo.

:: Start Frontend
echo  [1/1] Starting Frontend (React + Vite)...
cd /d "%~dp0frontend"
start cmd /k "title ADEIP Frontend && npm run dev"

:: Wait a moment then open browser
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo  Frontend running at: http://localhost:5173
echo.
echo  Close the terminal window to stop the server.
echo.
pause
