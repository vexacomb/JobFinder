import subprocess
import sys
import os
from pathlib import Path

VENV_DIR = ".venv"
VENV_PATH = Path(__file__).resolve().parent / VENV_DIR
REQUIREMENTS_FILE = "requirements.txt"

def run_command_with_feedback(command_args, cwd=None, venv_python_path=None):
    """Runs a command and prints its output line by line. Exits on error."""
    executable = command_args[0]
    if venv_python_path and (command_args[0] == "python" or command_args[0] == "pip"):
        # This logic helps select the venv python/pip if specified
        # but it's more robust to pass the full path to the venv executable directly
        pass # The full path should ideally be in command_args[0]

    print(f"Running: {' '.join(str(arg) for arg in command_args)}")
    try:
        # For Windows, use shell=True if activating venv commands or direct bat/cmd execution
        # However, for python/pip direct execution, it's often not needed and can be a security risk.
        # We are calling specific executables, so shell=False (default) is safer.
        process = subprocess.Popen(
            command_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            cwd=cwd
        )
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                print(line, end='')
            process.stdout.close()
        
        process.wait()
        
        if process.returncode != 0:
            print(f"\nError: Command failed with exit code {process.returncode}")
            sys.exit(process.returncode)
    except FileNotFoundError:
        print(f"\nError: Command not found: {command_args[0]}. Is it in your PATH or venv?")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)
    print("-" * 40)

def main():
    print("--- JobFinder Setup ---")

    # 1. Check for and create virtual environment if necessary
    if not VENV_PATH.is_dir():
        print(f"Creating virtual environment in '{VENV_DIR}'...")
        # sys.executable is the path to the python running this setup.py
        run_command_with_feedback([sys.executable, "-m", "venv", VENV_DIR])
        print(f"Virtual environment '{VENV_DIR}' created successfully.")
    else:
        print(f"Virtual environment '{VENV_DIR}' already exists.")

    # 2. Determine paths to Python and Pip within the virtual environment
    if sys.platform == "win32":
        venv_python = VENV_PATH / "Scripts" / "python.exe"
        venv_pip = VENV_PATH / "Scripts" / "pip.exe"
    else: # Linux, macOS
        venv_python = VENV_PATH / "bin" / "python"
        venv_pip = VENV_PATH / "bin" / "pip"

    if not venv_python.exists():
        print(f"Error: Python interpreter not found in virtual environment at '{venv_python}'.")
        sys.exit(1)
    if not venv_pip.exists():
        print(f"Error: Pip not found in virtual environment at '{venv_pip}'.")
        sys.exit(1)
    
    print(f"Using Python from venv: {venv_python}")

    # 3. Install dependencies from requirements.txt using venv's pip
    req_file_path = Path(__file__).resolve().parent / REQUIREMENTS_FILE
    if req_file_path.exists():
        print(f"Installing dependencies from '{REQUIREMENTS_FILE}' using venv pip...")
        run_command_with_feedback([str(venv_pip), "install", "-r", str(req_file_path)])
        print("Dependencies installed successfully.")
    else:
        print(f"Warning: '{REQUIREMENTS_FILE}' not found. Skipping dependency installation.")
        print(f"Please ensure '{REQUIREMENTS_FILE}' is in the same directory as setup.py.")

    # 4. Initialize the database using venv's python
    # This command runs: .venv/Scripts/python.exe -c "import database; database.init_db()"
    print("Initializing database...")
    # We need to ensure that the JobFinder modules (like 'database') are findable.
    # Running the command with the project root as CWD helps.
    project_root_dir = Path(__file__).resolve().parent
    run_command_with_feedback([
        str(venv_python),
        "-c",
        "import sys; sys.path.insert(0, ''); import database; database.init_db(); print(f'Database initialized at: {database.DB_PATH.resolve()}')"
    ], cwd=str(project_root_dir))
    print("Database initialization step complete.")
    
    print("\n--- Setup Complete! ---")
    print("You can now run the application using one of the following methods:")
    if sys.platform == "win32":
        print(f"  1. Activate venv manually: .\\{VENV_DIR}\\Scripts\\activate")
        print(f"     Then run: python main.py")
        print(f"  2. Or use the 'run_app.bat' script (if provided).")
    else:
        print(f"  1. Activate venv manually: source ./{VENV_DIR}/bin/activate")
        print(f"     Then run: python main.py")
        print(f"  2. Or use the 'run_app.sh' script (if provided).")

if __name__ == "__main__":
    main()