# config.py
from pathlib import Path
from functools import lru_cache

try:
    import tomllib            # Python 3.11+
except ModuleNotFoundError:    # 3.8–3.10
    import tomli as tomllib    # pip install tomli

@lru_cache(maxsize=1)
def load(path: str | Path = "config.toml") -> dict:
    """Load and cache the TOML config."""
    with Path(path).expanduser().open("rb") as f:
        return tomllib.load(f)
