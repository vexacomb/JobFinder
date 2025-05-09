import streamlit as st
from pathlib import Path
import toml
from dotenv import get_key, set_key, find_dotenv # find_dotenv is no longer needed here directly for path
from utils import CONFIG_FILE_PATH, ENV_FILE_PATH # MODIFIED: Import from utils.py

# --- File Paths ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE_PATH = PROJECT_ROOT / "config.toml"
found_env_path_str = find_dotenv(filename='.env', raise_error_if_not_found=False, usecwd=True)

if found_env_path_str:  # If a .env file was found by find_dotenv
    ENV_FILE_PATH = Path(found_env_path_str)  # Convert the found string path to a Path object
else:  # If .env is not found, default to creating/using it in the project root
    ENV_FILE_PATH = PROJECT_ROOT / ".env"



# --- Helper Functions for Config (load_config_data, save_config_data, get_default_config_structure) ---
# (These remain unchanged from the previous version)
def load_config_data(file_path: Path) -> dict:
    if file_path.exists():
        try:
            with file_path.open("r", encoding="utf-8") as f:
                return toml.load(f)
        except Exception as e:
            st.error(f"Error loading config file '{file_path}': {e}")
            return {} 
    return {}

def save_config_data(file_path: Path, data: dict):
    try:
        with file_path.open("w", encoding="utf-8") as f:
            toml.dump(data, f)
        st.toast(f"TOML Configuration saved to '{file_path.name}'!", icon="✅")
    except Exception as e:
        st.error(f"Error saving TOML config file '{file_path}': {e}")

def get_default_config_structure() -> dict:
    return {
        "locations": ["remote", "City, State, Country"],
        "keywords": ["Keyword1", "Keyword2"],
        "exclusions": ["Senior", "Lead", "Manager", "Clearance"],
        "default_resume": "Paste your default resume text here...\n\nTechnical Skills\n...\n\nProfessional Experience\n...",
        "prompt": "MUST-HAVE Criteria (job must meet ALL of these):\n1. ...\n\nFLEXIBLE Criteria:\n...\n\nDo NOT reject the job solely for:\n..."
    }

# --- Helper functions for .env file ---
def load_env_vars(env_path: Path) -> dict:
    """Loads specified API keys from the .env file."""
    keys_to_load = ["GOOGLE_API_KEY", "OPENAI_API_KEY"]
    loaded_vars = {}
    if env_path.exists():
        for key in keys_to_load:
            value = get_key(str(env_path), key)
            loaded_vars[key] = value if value else "" # Ensure empty string if key not found or None
    else: # If .env file doesn't exist, return empty strings for keys
        for key in keys_to_load:
            loaded_vars[key] = ""
    return loaded_vars

def save_env_vars(env_path: Path, vars_to_save: dict):
    """Saves API keys to the .env file."""
    try:
        # Ensure the .env file exists, create if not
        if not env_path.exists():
            env_path.touch() 
            st.info(f"Created new .env file at: {env_path}")

        for key, value in vars_to_save.items():
            if value and value.strip(): # Only save if value is not empty or just whitespace
                set_key(str(env_path), key, value)
            else: # If value is empty, consider removing the key or saving an empty value
                  # For simplicity, let's save an empty value if the user clears it,
                  # or we could use unset_key if python-dotenv supports it easily.
                  # set_key with an empty value might be fine, or use unset_key(str(env_path), key)
                set_key(str(env_path), key, "") # Save as empty if cleared by user
        st.toast("API Keys saved to .env file!", icon="🔑")
        return True
    except Exception as e:
        st.error(f"Error saving API keys to .env file: {e}")
        return False

# --- Streamlit Page Layout for "Inputs" ---
st.title("⚙️ JobFinder - Configuration")


# --- Sidebar Actions ---
with st.sidebar:
    st.header("Configuration Actions")
    st.markdown("---")
    if st.button("💾 Save All Settings", key="save_all_settings_sidebar_button", help="Save TOML configuration and API Keys.", use_container_width=True):
        # Assume widget keys are: locations_text_area, keywords_text_area, etc.
        # and google_api_key_input, openai_api_key_input
        
        # TOML Config Saving
        if all(k in st.session_state for k in ["locations_text_area", "keywords_text_area", "exclusions_text_area", "default_resume_text_area", "ai_prompt_text_area"]):
            updated_config_data = {
                "locations": [loc.strip() for loc in st.session_state.locations_text_area.splitlines() if loc.strip()],
                "keywords": [kw.strip() for kw in st.session_state.keywords_text_area.splitlines() if kw.strip()],
                "exclusions": [ex.strip() for ex in st.session_state.exclusions_text_area.splitlines() if ex.strip()],
                "default_resume": st.session_state.default_resume_text_area,
                "prompt": st.session_state.ai_prompt_text_area,
            }
            save_config_data(CONFIG_FILE_PATH, updated_config_data)
            st.session_state.config_just_saved_inputs_page = True # For TOML reload
        else:
            st.warning("Could not save TOML config: some input fields are not yet available.")

        # API Keys Saving
        api_keys_to_save = {}
        if "google_api_key_input" in st.session_state:
            api_keys_to_save["GOOGLE_API_KEY"] = st.session_state.google_api_key_input
        if "openai_api_key_input" in st.session_state: # If you add an OpenAI key field
            api_keys_to_save["OPENAI_API_KEY"] = st.session_state.openai_api_key_input
        
        if api_keys_to_save:
            save_env_vars(ENV_FILE_PATH, api_keys_to_save)
            st.session_state.apikeys_just_saved_inputs_page = True # For API key field reload
        
        st.rerun()
    st.markdown("---")


# --- Load Config Data (TOML) ---
if 'config_just_saved_inputs_page' not in st.session_state:
    st.session_state.config_just_saved_inputs_page = False
if 'apikeys_just_saved_inputs_page' not in st.session_state:
    st.session_state.apikeys_just_saved_inputs_page = False


config_data = load_config_data(CONFIG_FILE_PATH)
if st.session_state.config_just_saved_inputs_page:
    config_data = load_config_data(CONFIG_FILE_PATH)
    st.session_state.config_just_saved_inputs_page = False
if not config_data:
    if not CONFIG_FILE_PATH.exists():
        st.info(f"`{CONFIG_FILE_PATH.name}` not found. Displaying default structure. Save to create/update.")
    else:
        st.warning(f"Could not properly load `{CONFIG_FILE_PATH.name}` or it's empty. Displaying default. Saving will overwrite.")
    config_data = get_default_config_structure()

# --- Load API Keys (.env) ---
env_vars = load_env_vars(ENV_FILE_PATH)
if st.session_state.apikeys_just_saved_inputs_page: # Re-load if just saved
    env_vars = load_env_vars(ENV_FILE_PATH)
    st.session_state.apikeys_just_saved_inputs_page = False

# --- Define field values for text areas ---
locations_str_val = "\n".join(config_data.get("locations", []))
keywords_str_val = "\n".join(config_data.get("keywords", []))
exclusions_str_val = "\n".join(config_data.get("exclusions", []))
default_resume_val = config_data.get("default_resume", "")
ai_prompt_val = config_data.get("prompt", "")

google_api_key_val = env_vars.get("GOOGLE_API_KEY", "")
openai_api_key_val = env_vars.get("OPENAI_API_KEY", "") # If you add OpenAI

# --- Editable Fields (Main Page Area) ---
st.header("🔑 API Keys Management")
st.info(f"API Keys are stored in the `.env` file. When running as a packaged app, this file should be alongside the executable. Path: `{ENV_FILE_PATH}`")
st.text_input(
    "🔑 Google API Key (Gemini)",
    value=google_api_key_val,
    type="password",
    help="Your Google API key for Gemini AI.",
    key="google_api_key_input"
)
# Example if you were to add OpenAI key input
# st.text_input(
#     "🔑 OpenAI API Key",
#     value=openai_api_key_val,
#     type="password",
#     help="Your OpenAI API key.",
#     key="openai_api_key_input"
# )
st.markdown("---")

st.header("📝 Search Parameters (config.toml)")
# (Text areas for locations, keywords, exclusions as before, using their respective _val and keys)
st.text_area("📍 Locations", value=locations_str_val, height=100, key="locations_text_area")
st.text_area("🔑 Keywords", value=keywords_str_val, height=150, key="keywords_text_area")
st.text_area("🚫 Exclusion Keywords", value=exclusions_str_val, height=150, key="exclusions_text_area")

st.header("🧠 AI Evaluation Settings (config.toml)")
# (Text areas for default_resume, ai_prompt as before, using their respective _val and keys)
st.text_area("📄 Default Resume Text", value=default_resume_val, height=300, key="default_resume_text_area")
st.text_area("🤖 AI Evaluation Prompt", value=ai_prompt_val, height=300, key="ai_prompt_text_area")

st.markdown("---")
st.caption("Note: Changes to TOML configuration will be used the next time a job scan is initiated. API Key changes may require an application restart.")