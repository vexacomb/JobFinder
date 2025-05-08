import subprocess
import sys
from pathlib import Path

# This script now primarily launches the Streamlit dashboard.
# The actual application logic (scraping, database interaction)
# will be invoked from the dashboard or other modules.

def launch_dashboard():
    """
    Launches the Streamlit dashboard.
    """
    dashboard_script_path = Path(__file__).resolve().parent / "01_Dashboard.py"
    
    if not dashboard_script_path.exists():
        print(f"Error: Dashboard script not found at {dashboard_script_path}")
        print("Please ensure 'dashboard.py' is in the project root directory.")
        sys.exit(1)

    # If using a venv and runner scripts, setup.py ensures streamlit is in the venv.
    # The runner scripts (run_app.bat/sh) would call this main.py using the venv python.
    # So, sys.executable should point to the venv's python.
    # We can find streamlit executable relative to sys.executable or hope it's in PATH.
    # A more robust way if venv is well-defined:
    venv_dir = Path(__file__).resolve().parent / ".venv"
    if sys.platform == "win32":
        streamlit_exe = venv_dir / "Scripts" / "streamlit.exe"
    else:
        streamlit_exe = venv_dir / "bin" / "streamlit"

    if not streamlit_exe.exists():
        # Fallback to assuming streamlit is in PATH (less reliable for isolated envs)
        streamlit_exe = "streamlit" 
        print(f"Warning: Streamlit executable not found in .venv, trying global 'streamlit'.")

    command = [str(streamlit_exe), "run", str(dashboard_script_path)]

    print(f"Launching dashboard with command: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print(f"Error: Failed to find '{streamlit_exe}'. Is Streamlit installed and in your PATH or venv?")
        print(f"Please ensure setup.py has run successfully and your venv is correctly used.")
    except subprocess.CalledProcessError as e:
        print(f"Error launching dashboard: {e}")
    except KeyboardInterrupt:
        print("\nDashboard launch interrupted by user.")
    finally:
        print("Dashboard closed or failed to launch.")

if __name__ == "__main__":
    # Database initialization is now part of setup.py and can also be
    # triggered from the dashboard if needed for specific actions.
    # For now, setup.py handles initial DB creation.
    launch_dashboard()