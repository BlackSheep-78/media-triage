@echo off
REM =================================================================================
REM Project     : Media Triage
REM File        : run.bat
REM Description : Batch launcher that runs triage.py using python_path from config.json in PowerShell
REM Author      : Jorge (Blacksheep)
REM Created     : 2025-05-20
REM =================================================================================

for /f "usebackq tokens=*" %%A in (`powershell -NoProfile -Command ^
  "(Get-Content config.json | ConvertFrom-Json).python_path"`) do set PYTHON=%%A

if "%PYTHON%"=="" (
    echo [ERROR] Could not read python_path from config.json
    pause
    exit /b
)

echo Launching Media Triage in PowerShell...
powershell -NoProfile -Command "& { & '%PYTHON%' 'triage.py'; pause }"
