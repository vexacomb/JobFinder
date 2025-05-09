# utils.py
import sys
from pathlib import Path

def get_application_path() -> Path:
    """
    Returns the base path for the application, whether running as a script or a frozen PyInstaller bundle.
    """
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, sys.executable is the path to the exe.
        # The base path for data files is the directory containing the exe.
        application_path = Path(sys.executable).resolve().parent
    else:
        # If running as a script, __file__ is the path to this utils.py script.
        # We want the project root, which is one level up from where utils.py is if it's in the root.
        # Or, more generally, if utils.py is in the root, its parent is the project root.
        # This assumes utils.py is in the project's root directory.
        application_path = Path(__file__).resolve().parent
    return application_path

# Define common paths based on the application path
APP_ROOT = get_application_path()
CONFIG_FILE_PATH = APP_ROOT / "config.toml"
# ENV_FILE_PATH = APP_ROOT / ".env" # .env file is no longer primary for API keys
DB_PATH = APP_ROOT / "database.db" # Assuming database.db is also in the root

# Removed .env file creation logic as it's no longer central to API key management.

# Test (optional, run python utils.py to see the paths)
if __name__ == '__main__':
    print(f"Application Root: {APP_ROOT}")
    print(f"Config File Path: {CONFIG_FILE_PATH}")
    # print(f"Env File Path: {ENV_FILE_PATH}") # Commented out as ENV_FILE_PATH is removed
    print(f"Database Path: {DB_PATH}")
