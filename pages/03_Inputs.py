import streamlit as st
from pathlib import Path
import toml
# from dotenv import get_key, set_key, find_dotenv # No longer needed for .env specific operations here
from utils import CONFIG_FILE_PATH # Use paths from utils
# from config import load as load_main_config # For cache clearing
from config import load # Use direct import

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
        # load_main_config.cache_clear() # Now refers to load directly, still no cache_clear

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
        },
        "general": { # ADDED
            "ai_provider": "gemini" # ADDED
        }
    }

# --- Validation for Imported Config ---
def is_valid_config_structure(imported_data: dict) -> tuple[bool, str]:
    default_structure = get_default_config_structure()
    
    # Check top-level keys
    for key in default_structure.keys():
        if key not in imported_data:
            return False, f"Missing top-level key: '{key}'"
        if not isinstance(imported_data[key], type(default_structure[key])):
            return False, f"Invalid type for top-level key '{key}'. Expected {type(default_structure[key]).__name__}, got {type(imported_data[key]).__name__}."

    # Check nested structures and types
    # Search Parameters
    sp_default = default_structure["search_parameters"]
    sp_imported = imported_data["search_parameters"]
    for sp_key in sp_default.keys():
        if sp_key not in sp_imported:
            return False, f"Missing key in 'search_parameters': '{sp_key}'"
        if not isinstance(sp_imported[sp_key], list):
             return False, f"Key '{sp_key}' in 'search_parameters' should be a list."
        if not all(isinstance(item, str) for item in sp_imported[sp_key]):
            return False, f"All items in '{sp_key}' under 'search_parameters' should be strings."

    # Resume
    if "resume" not in imported_data or not isinstance(imported_data["resume"], dict):
        return False, "Missing 'resume' section or it's not a dictionary."
    resume_imported = imported_data["resume"]
    if "text" not in resume_imported:
        return False, "Missing 'text' key in 'resume' section."
    if not isinstance(resume_imported["text"], str):
        return False, "'resume.text' must be a string."

    # Prompts
    if "prompts" not in imported_data or not isinstance(imported_data["prompts"], dict):
        return False, "Missing 'prompts' section or it's not a dictionary."
    prompts_imported = imported_data["prompts"]
    if "evaluation_prompt" not in prompts_imported:
        return False, "Missing 'evaluation_prompt' key in 'prompts' section."
    if not isinstance(prompts_imported["evaluation_prompt"], str):
        return False, "'prompts.evaluation_prompt' must be a string."

    # API Keys
    if "api_keys" not in imported_data or not isinstance(imported_data["api_keys"], dict):
        return False, "Missing 'api_keys' section or it's not a dictionary."
    api_keys_imported = imported_data["api_keys"]
    api_keys_default = default_structure["api_keys"]
    for api_key_name in api_keys_default.keys():
        if api_key_name not in api_keys_imported:
            return False, f"Missing API key '{api_key_name}' in 'api_keys' section."
        if not isinstance(api_keys_imported[api_key_name], str):
            return False, f"API key '{api_key_name}' must be a string."
            
    # General Settings # ADDED
    if "general" not in imported_data or not isinstance(imported_data["general"], dict): # ADDED
        return False, "Missing 'general' section or it's not a dictionary." # ADDED
    general_imported = imported_data["general"] # ADDED
    general_default = default_structure["general"] # ADDED
    for general_key_name in general_default.keys(): # ADDED
        if general_key_name not in general_imported: # ADDED
            return False, f"Missing setting '{general_key_name}' in 'general' section." # ADDED
        if not isinstance(general_imported[general_key_name], str): # ADDED
            return False, f"Setting '{general_key_name}' in 'general' section must be a string." # ADDED
        if general_key_name == "ai_provider" and general_imported[general_key_name] not in ["gemini", "openai"]: # ADDED
             return False, "ai_provider in general section must be either 'gemini' or 'openai'." # ADDED
            
    return True, "Configuration structure is valid."


# --- Helper functions for .env file ---
# Removing load_env_vars and save_env_vars as API keys are now in config.toml

# --- Streamlit Page Layout for "Inputs" ---
st.title("⚙️ JobFinder - Configuration")


# --- Sidebar Actions ---
with st.sidebar:
    st.header("Configuration Actions")

    # --- Save All Settings Button (MOVED UP) ---
    if st.button("💾 Save All Settings", key="save_all_settings_sidebar_button", help="Save TOML configuration including API Keys.", use_container_width=True):
        
        # TOML Config Saving (including API Keys)
        required_toml_keys = [
            "locations_text_area", "keywords_text_area", 
            "exclusions_text_area", "default_resume_text_area", 
            "ai_prompt_text_area", "google_api_key_input", "openai_api_key_input",
            "ai_provider_select" 
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
                },
                "general": { 
                    "ai_provider": st.session_state.ai_provider_select 
                }
            }
            save_config_data(CONFIG_FILE_PATH, updated_config_data) 
            st.session_state.config_just_saved_inputs_page = True 
        else:
            missing_keys = [k for k in required_toml_keys if k not in st.session_state]
            st.warning(f"Could not save configuration: some input fields are not yet available. Missing: {', '.join(missing_keys)}")
        
        st.rerun()

    # --- Export Button ---
    try:
        with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
            config_content_for_export = f.read()
        st.download_button(
            label="📤 Export Configuration",
            data=config_content_for_export,
            file_name="jobfinder_config.toml", 
            mime="application/toml",
            use_container_width=True,
            help="Download the current configuration as a TOML file."
        )
    except FileNotFoundError:
        st.warning(f"`{CONFIG_FILE_PATH.name}` not found. Save settings first to create it.")
    except Exception as e:
        st.error(f"Could not read config for export: {e}")

    # --- Import Configuration ---
    if 'show_config_uploader' not in st.session_state:
        st.session_state.show_config_uploader = False

    if st.button("📥 Import Configuration", use_container_width=True, key="show_config_uploader_button", help="Click to reveal the uploader, then select a TOML configuration file."):
        st.session_state.show_config_uploader = True

    if st.session_state.show_config_uploader:
        uploaded_file = st.file_uploader(
            "Upload Configuration File",
            type=["toml"],
            key="config_file_uploader_widget",
            help="Upload a TOML configuration file. This will overwrite current settings if valid.",
            label_visibility="collapsed"
        )

        if uploaded_file is not None:
            try:
                imported_content = uploaded_file.getvalue().decode("utf-8")
                imported_data = toml.loads(imported_content)
                
                is_valid, message = is_valid_config_structure(imported_data)
                
                if is_valid:
                    save_config_data(CONFIG_FILE_PATH, imported_data)
                    st.session_state.config_just_saved_inputs_page = True 
                    st.success("Configuration imported successfully and saved!")
                    st.session_state.import_error_message = None 
                else:
                    st.session_state.import_error_message = f"Invalid configuration file: {message}"
            except toml.TomlDecodeError:
                st.session_state.import_error_message = "Invalid TOML format in the uploaded file."
            except Exception as e:
                st.session_state.import_error_message = f"Error processing uploaded file: {e}"
            finally:
                st.session_state.show_config_uploader = False
                st.rerun() 

    if "import_error_message" in st.session_state and st.session_state.import_error_message:
        st.error(st.session_state.import_error_message)
        st.session_state.import_error_message = None
    
    st.markdown("---") # ADDED separator before AI settings

    # --- AI Provider Selection (MOVED DOWN) ---
    st.subheader("AI Settings") 
    current_config_for_radio = load_config_data(CONFIG_FILE_PATH) 
    current_ai_provider = current_config_for_radio.get("general", {}).get("ai_provider", "gemini") 
    ai_provider_options = ["gemini", "openai"] 
    
    selected_ai_provider = st.radio( 
        "Choose AI Provider:", 
        options=ai_provider_options, 
        index=ai_provider_options.index(current_ai_provider) if current_ai_provider in ai_provider_options else 0, 
        key="ai_provider_select", 
        help="Select the AI provider for job evaluation. This setting is saved when you click 'Save All Settings'." 
    ) 


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
st.markdown("[How to get a Google Gemini API key](https://ai.google.dev/gemini-api/docs/api-key)")

st.text_input(
    "🔑 OpenAI API Key", # Assuming you want to keep this field functional
    value=openai_api_key_val,
    type="password",
    help="Your OpenAI API key.",
    key="openai_api_key_input"
)
st.markdown("[How to get an OpenAI API key](https://www.pickaxeproject.com/post/how-to-get-your-openai-api-key-a-step-by-step-guide)")
st.markdown("---")

st.header("📝 Search Parameters")
st.text_area("📍 Locations", value=locations_str_val, height=100, key="locations_text_area")
st.text_area("🔑 Keywords", value=keywords_str_val, height=150, key="keywords_text_area")
st.text_area("🚫 Exclusion Keywords", value=exclusions_str_val, height=150, key="exclusions_text_area")

st.header("✨ AI Evaluation Settings")
st.text_area("📄 Resume Text", value=default_resume_val, height=300, key="default_resume_text_area")
st.text_area("🤖 AI Prompt", value=ai_prompt_val, height=300, key="ai_prompt_text_area")

