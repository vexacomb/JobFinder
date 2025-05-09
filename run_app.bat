@echo off
REM Activates the virtual environment and runs the main application script.

REM Get the directory of this batch script
set "SCRIPT_DIR=%~dp0"
REM Remove trailing backslash if present, for robust path joining
IF "%SCRIPT_DIR:~-1%"=="\" SET "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo "DEBUG: SCRIPT_DIR is "%SCRIPT_DIR%"

set "VENV_DIR=%SCRIPT_DIR%\.venv"
echo "DEBUG: VENV_DIR is "%VENV_DIR%"

set "ACTIVATION_SCRIPT=%VENV_DIR%\Scripts\activate.bat"
echo "DEBUG: ACTIVATION_SCRIPT is "%ACTIVATION_SCRIPT%"

set "MAIN_PY=%SCRIPT_DIR%\main.py"
echo "DEBUG: MAIN_PY is "%MAIN_PY%"

echo "Checking for virtual environment activation script..."
IF EXIST "%ACTIVATION_SCRIPT%" (
    echo "Activation script found at "%ACTIVATION_SCRIPT%"
    echo "Activating virtual environment..."
    CALL "%ACTIVATION_SCRIPT%"
    IF DEFINED VIRTUAL_ENV (
        echo "Virtual environment activated."
        echo "Launching JobFinder using Python from activated .venv..."
        python "%MAIN_PY%"
    ) ELSE (
        echo "ERROR: Virtual environment activation failed unexpectedly after calling activate.bat."
        echo "Check if the activate.bat script is corrupted or if there are issues with your venv setup."
        pause
        exit /b 1
    )
) ELSE (
    echo "Virtual environment activation script ("%ACTIVATION_SCRIPT%") not found."
    echo "Please run setup.py first to create the virtual environment and install dependencies."
    pause
    exit /b 1
)

echo.
echo "JobFinder has finished or an error occurred."
REM If venv was activated, it typically deactivates when cmd session ends or by explicitly calling deactivate
REM For simplicity, we rely on cmd session termination here.
REM Add 'call deactivate' here if you want explicit deactivation before script ends.
pause