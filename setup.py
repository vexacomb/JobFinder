"""
setup.py
Bootstraps a clean clone of JobFinder.

* Installs PyPI dependencies if missing.
* Creates jobfinder.db and the required tables.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
REQUIRED_PYPI = [
    "requests",
    "beautifulsoup4",
    # tomli is only needed on Python < 3.11
    *(["tomli"] if sys.version_info < (3, 11) else []),
]
PROJECT_ROOT = Path(__file__).parent


def ensure_packages() -> None:
    for pkg in REQUIRED_PYPI:
        if importlib.util.find_spec(pkg) is None:
            print(f"Installing missing dependency: {pkg} …")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])


def main() -> None:
    ensure_packages()

    # local import now that dependencies are guaranteed
    import database  # noqa: 402  (placed here to avoid early import errors)

    database.init_db()
    print("✔ All dependencies present")
    print(f"✔ Database initialised at {database.DB_PATH.resolve()}")
    print("\nYou’re ready – run  python main.py")


if __name__ == "__main__":
    main()
