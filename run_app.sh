#!/bin/bash
# Activates the virtual environment (implicitly by calling venv python) and runs the main application script.

# Get the absolute directory of this bash script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
MAIN_PY="$SCRIPT_DIR/main.py"

echo "Checking for virtual environment Python executable..."
if [ ! -f "$VENV_PYTHON" ]; then
    echo "Virtual environment's Python ($VENV_PYTHON) not found."
    echo "Please run setup.py first to create the virtual environment and install dependencies."
    exit 1
fi

echo "Launching JobFinder using Python from .venv..."
"$VENV_PYTHON" "$MAIN_PY"

echo ""
echo "JobFinder has finished."