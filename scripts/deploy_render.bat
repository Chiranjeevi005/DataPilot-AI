@echo off
echo Deploying to Render...

WHERE render >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Error: 'render' CLI not found.
    echo Please install it via 'npm install -g @render/cli' or official installer.
    exit /b 1
)

echo Creating/Updating Blueprint from render.yaml...
call render blueprints create --file render.yaml --yes

if %ERRORLEVEL% NEQ 0 (
    echo Deployment failed or blueprint already exists.
    echo Try 'render blueprints list' to see existing blueprints.
    echo If it exists, use 'render blueprints apply --file render.yaml' (if supported) or use the dashboard.
) else (
    echo Deployment triggered!
)
pause
