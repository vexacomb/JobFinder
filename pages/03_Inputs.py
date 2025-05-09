import streamlit as st
from pathlib import Path
import toml
# from dotenv import get_key, set_key, find_dotenv # No longer needed for .env specific operations here
from utils import CONFIG_FILE_PATH # Use paths from utils
from config import load as load_main_config # For cache clearing

# --- File Paths ---
# PROJECT_ROOT = Path(__file__).resolve().parent.parent # Use utils.APP_ROOT if a generic root is needed elsewhere
# CONFIG_FILE_PATH is imported from utils
# ENV_FILE_PATH is imported from utils (though less relevant now for API keys)


# --- Helper Functions for Config (load_config_data, save_config_data, get_default_config_structure) ---
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
        st.toast(f"Configuration saved to '{file_path.name}'!", icon="✅")
        # Clear the cache of the main config loader
        load_main_config.cache_clear()
        st.toast("Configuration cache cleared.", icon="♻️")

    except Exception as e:
        st.error(f"Error saving TOML config file '{file_path}': {e}")

def get_default_config_structure() -> dict: # Updated default structure
    return {
        "search_parameters": {
            "locations": ["remote", "City, State, Country"],
            "keywords": ["Keyword1", "Keyword2"],
            "exclusion_keywords": ["Senior", "Lead", "Manager", "Clearance"], # Changed 'exclusions' to 'exclusion_keywords' for consistency
        },
        "resume": {
            "text": "Paste your default resume text here...\n\nTechnical Skills\n...\n\nProfessional Experience\n..."
        },
        "prompts": {
             "evaluation_prompt": "MUST-HAVE Criteria (job must meet ALL of these):\n1. ...\n\nFLEXIBLE Criteria:\n...\n\nDo NOT reject the job solely for:\n..."
        },
        "api_keys": { # Added API keys section
            "google_api_key": "YOUR_GOOGLE_API_KEY_HERE",
            "openai_api_key": "YOUR_OPENAI_API_KEY_HERE"
        }
    }

# --- Helper functions for .env file ---
# Removing load_env_vars and save_env_vars as API keys are now in config.toml

# --- Streamlit Page Layout for "Inputs" ---
st.title("⚙️ JobFinder - Configuration")


# --- Sidebar Actions ---
with st.sidebar:
    st.header("Configuration Actions")
    if st.button("💾 Save All Settings", key="save_all_settings_sidebar_button", help="Save TOML configuration including API Keys.", use_container_width=True):
        
        # TOML Config Saving (including API Keys)
        required_toml_keys = [
            "locations_text_area", "keywords_text_area", 
            "exclusions_text_area", "default_resume_text_area", 
            "ai_prompt_text_area", "google_api_key_input", "openai_api_key_input"
        ]
        if all(k in st.session_state for k in required_toml_keys):
            updated_config_data = {
                "search_parameters": {
                    "locations": [loc.strip() for loc in st.session_state.locations_text_area.splitlines() if loc.strip()],
                    "keywords": [kw.strip() for kw in st.session_state.keywords_text_area.splitlines() if kw.strip()],
                    "exclusion_keywords": [ex.strip() for ex in st.session_state.exclusions_text_area.splitlines() if ex.strip()],
                },
                "resume": {
                    "text": st.session_state.default_resume_text_area
                },
                "prompts": {
                    "evaluation_prompt": st.session_state.ai_prompt_text_area
                },
                "api_keys": {
                    "google_api_key": st.session_state.google_api_key_input,
                    "openai_api_key": st.session_state.openai_api_key_input
                }
            }
            save_config_data(CONFIG_FILE_PATH, updated_config_data) # CONFIG_FILE_PATH from utils
            st.session_state.config_just_saved_inputs_page = True 
        else:
            missing_keys = [k for k in required_toml_keys if k not in st.session_state]
            st.warning(f"Could not save configuration: some input fields are not yet available. Missing: {', '.join(missing_keys)}")
        
        st.rerun()


# --- Load Config Data (TOML) ---
if 'config_just_saved_inputs_page' not in st.session_state:
    st.session_state.config_just_saved_inputs_page = False

config_data = load_config_data(CONFIG_FILE_PATH) # CONFIG_FILE_PATH from utils
if st.session_state.config_just_saved_inputs_page:
    config_data = load_config_data(CONFIG_FILE_PATH) # Re-load if just saved
    st.session_state.config_just_saved_inputs_page = False

if not config_data: # If loading failed or file doesn't exist
    default_structure = get_default_config_structure()
    if not CONFIG_FILE_PATH.exists():
        st.info(f"`{CONFIG_FILE_PATH.name}` not found. Displaying default structure. Save to create/update.")
        config_data = default_structure
    else: # File exists but was empty or failed to load
        st.warning(f"Could not properly load `{CONFIG_FILE_PATH.name}` or it's empty. Displaying default. Saving will overwrite.")
        config_data = default_structure


# --- Define field values for UI elements from config_data ---
search_params = config_data.get("search_parameters", {})
locations_str_val = "\n".join(search_params.get("locations", []))
keywords_str_val = "\n".join(search_params.get("keywords", []))
exclusions_str_val = "\n".join(search_params.get("exclusion_keywords", [])) # ensure key matches default

resume_data = config_data.get("resume", {})
default_resume_val = resume_data.get("text", "")

prompts_data = config_data.get("prompts", {})
ai_prompt_val = prompts_data.get("evaluation_prompt", "")

api_keys_data = config_data.get("api_keys", {}) # Get API keys section
google_api_key_val = api_keys_data.get("google_api_key", "")
openai_api_key_val = api_keys_data.get("openai_api_key", "")


# --- Editable Fields (Main Page Area) ---
st.header("🔑 API Keys Management") # Updated header
st.text_input(
    "🔑 Google API Key (Gemini)",
    value=google_api_key_val,
    type="password",
    help="Your Google API key for Gemini AI.",
    key="google_api_key_input"
)
st.text_input(
    "🔑 OpenAI API Key", # Assuming you want to keep this field functional
    value=openai_api_key_val,
    type="password",
    help="Your OpenAI API key.",
    key="openai_api_key_input"
)
st.markdown("---")

st.header("📝 Search Parameters")
st.text_area("📍 Locations", value=locations_str_val, height=100, key="locations_text_area")
st.text_area("🔑 Keywords", value=keywords_str_val, height=150, key="keywords_text_area")
st.text_area("🚫 Exclusion Keywords", value=exclusions_str_val, height=150, key="exclusions_text_area")

st.header("✨ AI Evaluation Settings")
st.text_area("📄 Resume Text", value=default_resume_val, height=300, key="default_resume_text_area")
st.text_area("🤖 AI Prompt", value=ai_prompt_val, height=300, key="ai_prompt_text_area")

