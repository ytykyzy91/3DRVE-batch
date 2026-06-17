@echo off
setlocal

REM Run one RVE modelling/preprocessing case with JSON initialization overrides.
REM Edit RVE_TYPE, PARAMS_JSON, and OUTPUT_DIR below as needed.

cd /d "%~dp0"

set RVE_TYPE=orthogonal_weave_3d
set PARAMS_JSON=configs\model_params.example.json
set OUTPUT_DIR=data\intermediate\json_single_case

call "%USERPROFILE%\AppData\Local\miniconda3\condabin\conda.bat" activate py39
if errorlevel 1 (
    echo [ERROR] Failed to activate conda environment: py39
    pause
    exit /b 1
)

echo [INFO] Working directory: %CD%
echo [INFO] RVE_TYPE   = %RVE_TYPE%
echo [INFO] PARAMS_JSON= %PARAMS_JSON%
echo [INFO] OUTPUT_DIR = %OUTPUT_DIR%
echo [INFO] Running single-case modelling with JSON overrides...

python scripts\run_current_pipeline.py --rve-type %RVE_TYPE% --params-json "%PARAMS_JSON%" --output-dir "%OUTPUT_DIR%"
set RUN_EXIT_CODE=%ERRORLEVEL%

if not "%RUN_EXIT_CODE%"=="0" (
    echo [ERROR] Single-case run failed with exit code %RUN_EXIT_CODE%.
) else (
    echo [INFO] Single-case run finished successfully.
)

pause
exit /b %RUN_EXIT_CODE%
