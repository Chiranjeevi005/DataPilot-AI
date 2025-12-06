@echo off
echo ========================================
echo Restarting DataPilot AI
echo ========================================

echo.
echo Step 1: Stopping all processes...
taskkill /F /IM python.exe /IM node.exe 2>nul
timeout /t 2 >nul

echo.
echo Step 2: Starting application...
call start-app.bat

echo.
echo ========================================
echo Application restarted!
echo Frontend: http://localhost:3003
echo ========================================
