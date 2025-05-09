# config.py
from pathlib import Path
from functools import lru_cache
from utils import CONFIG_FILE_PATH # MODIFIED: Import from utils.py

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
import toml # For saving

DEFAULT_CONFIG = {
    "search_parameters": {
        "locations": ["Remote"],
        "keywords": ["Software Engineer", "Python Developer"],
        "exclusion_keywords": ["Senior", "Sr.", "Lead", "Manager"],
    },
    "resume": {
        "text": "Your resume text here. Paste your full resume or a summary."
    },
    "prompts": {
        "evaluation_prompt": """Analyze the following job description based on the provided resume.
Determine if the job is a good fit.
Consider the keywords, location, and exclusion keywords.
Provide a brief reason for your decision (approve or reject).
Output only 'approve' or 'reject' followed by a colon and the reason. Example: 'approve: The job matches the keywords and location, and the experience aligns with the resume.' or 'reject: The location is not remote and the experience level required is too high.'"""
    },
    "api_keys": { # New section for API keys
        "google_api_key": "YOUR_GOOGLE_API_KEY_HERE",
        "openai_api_key": "YOUR_OPENAI_API_KEY_HERE"
    }
}

def save_config(config_data: dict, path: Path = CONFIG_FILE_PATH):
    """Save the configuration data to the TOML file."""
    with path.expanduser().open("w", encoding="utf-8") as f: # Open in text mode for toml.dump
        toml.dump(config_data, f)

def create_default_config_if_not_exists(path: Path = CONFIG_FILE_PATH):
    """Creates a default config.toml file if it doesn't already exist."""
    if not path.expanduser().exists():
        print(f"config.toml not found at {path}. Creating a default config.toml.")
        save_config(DEFAULT_CONFIG, path)
        print(f"Default config.toml created at {path}. Please review and update it as needed.")

@lru_cache(maxsize=1)
def load(path: Path = CONFIG_FILE_PATH) -> dict:
    """Load and cache the TOML config. Ensures defaults are used if file is empty or malformed."""
    create_default_config_if_not_exists(path) # Ensures file exists if it was missing

    try:
        with path.expanduser().open("rb") as f:
            loaded_config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        print(f"Error decoding TOML from '{path}': {e}. Attempting to re-initialize with defaults.")
        loaded_config = {} # Treat as empty to trigger default re-initialization

    # Check if the loaded config is empty or missing essential structures
    if not loaded_config or "search_parameters" not in loaded_config:
        # This condition handles: an empty file, a TOMLDecodeError, or a valid TOML file missing critical keys.
        print(f"Warning: Configuration at '{path}' was empty, malformed, or incomplete. Re-initializing with default values and saving.")
        save_config(DEFAULT_CONFIG, path) # Save defaults to repair/initialize the file
        return DEFAULT_CONFIG.copy() # Return a copy of the defaults for current use
        
    return loaded_config