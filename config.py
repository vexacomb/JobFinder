# config.py
from pathlib import Path
from functools import lru_cache
from utils import CONFIG_FILE_PATH # MODIFIED: Import from utils.py

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

@lru_cache(maxsize=1)
def load(path: Path = CONFIG_FILE_PATH) -> dict: # MODIFIED: Default path from utils
    """Load and cache the TOML config."""
    # The expanduser() might not be relevant if path is always absolute from utils.py
    # but doesn't hurt.
    with path.expanduser().open("rb") as f: 
        return tomllib.load(f)