@echo off
setlocal

REM Run solver calculations for an existing generated batch.
REM Edit BATCH_DIR below to point to the batch you want to calculate.

cd /d "%~dp0"

set BATCH_DIR=output\orthogonal_weave_3d\batch0003
set SOLVER_EXE=D:\Demx_softwares\2025b\Virgo_R2025b_win64\bin\vg_solver.exe
set SOLVER_CONFIG=D:\Demx_softwares\2025C\Plexian_R2025c_fixed_win64\res\PlexianConfig.json

call "%USERPROFILE%\AppData\Local\miniconda3\condabin\conda.bat" activate py39
if errorlevel 1 (
    echo [ERROR] Failed to activate conda environment: py39
    pause
    exit /b 1
)

echo [INFO] Working directory: %CD%
echo [INFO] BATCH_DIR     = %BATCH_DIR%
echo [INFO] SOLVER_EXE    = %SOLVER_EXE%
echo [INFO] SOLVER_CONFIG = %SOLVER_CONFIG%
echo [INFO] Running solver for generated batch...

python scripts\run_batch_solver.py --batch-dir "%BATCH_DIR%" --solver-exe "%SOLVER_EXE%" --solver-config "%SOLVER_CONFIG%"
set RUN_EXIT_CODE=%ERRORLEVEL%

if not "%RUN_EXIT_CODE%"=="0" (
    echo [ERROR] Batch solver failed with exit code %RUN_EXIT_CODE%.
) else (
    echo [INFO] Batch solver finished.
)

pause
exit /b %RUN_EXIT_CODE%
