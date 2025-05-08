@echo off
REM Activates the virtual environment and runs the main application script.

REM Get the directory of this batch script
set "SCRIPT_DIR=%~dp0"
REM Ensure paths with spaces are handled by quoting, though SCRIPT_DIR usually doesn't have them.
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "MAIN_PY=%SCRIPT_DIR%main.py"

echo Checking for virtual environment and Python executable...
if not exist "%PYTHON_EXE%" (
    echo Virtual environment's Python (%PYTHON_EXE%) not found.
    echo Please run setup.py first to create the virtual environment and install dependencies.
    pause
    exit /b 1
)

echo Launching JobFinder using Python from .venv...
"%PYTHON_EXE%" "%MAIN_PY%"

echo.
echo JobFinder has finished. Press any key to exit.
pause