@echo off
echo Starting DataPilot AI Development Environment consistently...

:: 1. Start Backend API (Port 5328)
:: We use 'start' to open a new separate command window for each process
start "DataPilot Backend API" cmd /k "set PYTHONPATH=.&& .venv\Scripts\python.exe src/api/upload/route.py"

:: 2. Start Worker Process
start "DataPilot Worker" cmd /k "set PYTHONPATH=.&& .venv\Scripts\python.exe src/worker.py"

:: 3. Start Frontend (Port 3003)
:: Giving backend a moment to initialize
timeout /t 3 >nul
start "DataPilot Frontend" cmd /k "npm run dev"

echo ---------------------------------------------------
echo All services are launching in separate windows.
echo Frontend will be ready at: http://localhost:3003
echo ---------------------------------------------------
pause
