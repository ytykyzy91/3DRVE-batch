@echo off
setlocal

REM Run LHS DOE batch modelling from configs\batch_doe.example.json
REM Double-click this file, or run from cmd.

cd /d "%~dp0"

call "%USERPROFILE%\AppData\Local\miniconda3\condabin\conda.bat" activate py39
if errorlevel 1 (
    echo [ERROR] Failed to activate conda environment: py39
    pause
    exit /b 1
)

echo [INFO] Working directory: %CD%
echo [INFO] Running LHS DOE batch modelling...

python scripts\run_batch_doe.py --config configs\batch_doe.example.json
set RUN_EXIT_CODE=%ERRORLEVEL%

if not "%RUN_EXIT_CODE%"=="0" (
    echo [ERROR] LHS DOE batch failed with exit code %RUN_EXIT_CODE%.
) else (
    echo [INFO] LHS DOE batch finished successfully.
)

pause
exit /b %RUN_EXIT_CODE%
