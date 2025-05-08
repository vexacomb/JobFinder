import streamlit as st
from pathlib import Path
import toml

# --- Configuration File Path ---
CONFIG_FILE_PATH = Path(__file__).resolve().parent.parent / "config.toml"

# --- Helper Functions for Config (load_config_data, save_config_data, get_default_config_structure) ---
# (These functions remain unchanged)
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
        # Use st.toast for a less intrusive success message if desired, or stick to st.success
        st.toast(f"Configuration saved to '{file_path.name}'!", icon="✅")
        # st.success(f"Configuration saved successfully to '{file_path.name}'!") # Alternative
    except Exception as e:
        st.error(f"Error saving config file '{file_path}': {e}")

def get_default_config_structure() -> dict:
    return {
        "locations": ["remote", "City, State, Country"],
        "keywords": ["Keyword1", "Keyword2"],
        "exclusions": ["Senior", "Lead", "Manager", "Clearance"],
        "default_resume": "Paste your default resume text here...\n\nTechnical Skills\n...\n\nProfessional Experience\n...",
        "prompt": "MUST-HAVE Criteria (job must meet ALL of these):\n1. ...\n\nFLEXIBLE Criteria:\n...\n\nDo NOT reject the job solely for:\n..."
    }

# --- Streamlit Page Layout for "Inputs" ---
st.set_page_config(page_title="JobFinder Inputs", layout="wide") # Can be set in main app.py for consistency
st.title("⚙️ JobFinder - Configuration Inputs")

# --- Sidebar Save Button ---
# This section defines the save button logic in the sidebar
with st.sidebar:
    st.header("Configuration Actions")
    # Provide some space if other sidebar items exist above or for visual separation
    st.markdown("---") 
    if st.button("💾 Save Configuration", key="save_config_sidebar_button", help="Save all changes to config.toml", use_container_width=True):
        # Prepare data for saving using current session_state values of the input widgets
        # Ensure keys used here match the 'key' arguments of your st.text_area widgets below
        if all(k in st.session_state for k in ["locations_text_area", "keywords_text_area", "exclusions_text_area", "default_resume_text_area", "ai_prompt_text_area"]):
            updated_config_data = {
                "locations": [loc.strip() for loc in st.session_state.locations_text_area.splitlines() if loc.strip()],
                "keywords": [kw.strip() for kw in st.session_state.keywords_text_area.splitlines() if kw.strip()],
                "exclusions": [ex.strip() for ex in st.session_state.exclusions_text_area.splitlines() if ex.strip()],
                "default_resume": st.session_state.default_resume_text_area,
                "prompt": st.session_state.ai_prompt_text_area,
            }
            save_config_data(CONFIG_FILE_PATH, updated_config_data)
            # Set a flag to indicate a save happened, to potentially reload data or show persisted message
            st.session_state.config_just_saved_inputs_page = True 
            # Rerun to reflect any changes if save_config_data itself doesn't cause it
            # or if we need to update the displayed values from file.
            # The success/error messages are now handled within save_config_data using st.toast or st.error.
            # A rerun might be good if load_config_data is called again to refresh text areas.
            st.rerun()
        else:
            st.warning("Some input fields are not yet available in session state. Please ensure the page has fully loaded.")
    st.markdown("---")


# --- Load Config Data ---
# Initialize session state flag for this page specifically if not already done
if 'config_just_saved_inputs_page' not in st.session_state:
    st.session_state.config_just_saved_inputs_page = False

config_data = load_config_data(CONFIG_FILE_PATH)

# If a save just occurred on this page, reload data to ensure text areas are fresh
if st.session_state.config_just_saved_inputs_page:
    config_data = load_config_data(CONFIG_FILE_PATH)
    st.session_state.config_just_saved_inputs_page = False # Reset flag

# Handle case where config file is missing or empty after load attempt
if not config_data:
    if not CONFIG_FILE_PATH.exists():
        st.info(f"`{CONFIG_FILE_PATH.name}` not found. Displaying default structure. Save to create the file.")
    else:
        st.warning(f"Could not properly load `{CONFIG_FILE_PATH.name}` or it's empty. Displaying default structure. Saving will overwrite.")
    config_data = get_default_config_structure()


# --- Define field values for text areas ---
locations_str_val = "\n".join(config_data.get("locations", []))
keywords_str_val = "\n".join(config_data.get("keywords", []))
exclusions_str_val = "\n".join(config_data.get("exclusions", []))
default_resume_val = config_data.get("default_resume", "")
ai_prompt_val = config_data.get("prompt", "")

# --- Editable Fields (Main Page Area) ---
# Removed the "Manage the settings..." and "Full path to config file:" markdown lines

st.header("Search Parameters")
st.text_area( # Assign to new_... variables is not needed if directly accessed via key
    "📍 Locations (one per line)",
    value=locations_str_val,
    height=100,
    help="Enter geographical locations for job searches, or 'remote'.",
    key="locations_text_area" # Key for accessing value in session_state
)

st.text_area(
    "🔑 Keywords (one per line)",
    value=keywords_str_val,
    height=150,
    help="Enter job titles or keywords (e.g., 'SOC Analyst Tier 1', 'Cybersecurity Monitoring').",
    key="keywords_text_area"
)

st.text_area(
    "🚫 Exclusion Keywords (one per line)",
    value=exclusions_str_val,
    height=150,
    help="Keywords in job titles/descriptions that should exclude the job (e.g., 'Senior', 'Manager', 'TS/SCI').",
    key="exclusions_text_area"
)

st.header("AI Evaluation Settings")
st.text_area(
    "📄 Default Resume Text",
    value=default_resume_val,
    height=300,
    help="The resume text used by the AI to evaluate job description eligibility.",
    key="default_resume_text_area"
)

st.text_area(
    "🤖 AI Evaluation Prompt",
    value=ai_prompt_val,
    height=300,
    help="The system prompt given to the AI for evaluating jobs against your resume and criteria.",
    key="ai_prompt_text_area"
)

st.markdown("---")
st.caption("Note: Changes to the configuration will be used the next time a job scan is initiated.")
