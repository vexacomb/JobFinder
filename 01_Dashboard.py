import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
import html
import time # For potential use with st.empty and messages
import toml # Added for consistency, though not directly used for DB
import shutil # For file operations

# 1. Page Config FIRST
st.set_page_config(
    page_title="JobFinder Application", # A more global title
    layout="wide",
    initial_sidebar_state="expanded" # Optional: to have sidebar open by default
)

# 2. Standard Python Imports
import sqlite3
import pandas as pd
from pathlib import Path
import html
import time # For potential use with st.empty and messages

# 3. Define DB_PATH and other critical global-like variables from your modules.
#    Handle imports carefully.
DB_PATH = None # Initialize to None
scrape_phase = None
clear_all_approved_jobs = None
mark_job_as_applied = None
delete_approved_job = None

# Attempt to import the main config loader for cache management
try:
    from config import load as load_main_config
except ImportError:
    load_main_config = None # Fallback if config.py or load isn't found
    st.error("Failed to import config loader. Configuration reloading may not work as expected.")

try:
    from utils import DB_PATH as UTILS_DB_PATH # Use an alias
    DB_PATH = UTILS_DB_PATH # Assign to the global DB_PATH

    from database import init_db # Import init_db
    from database import clear_all_approved_jobs as db_clear_approved
    clear_all_approved_jobs = db_clear_approved

    from database import mark_job_as_applied as db_mark_applied
    mark_job_as_applied = db_mark_applied

    from database import delete_approved_job as db_delete_approved
    delete_approved_job = db_delete_approved
    
    from scrape import scrape_phase as sp_scrape_phase
    scrape_phase = sp_scrape_phase

    # ADDED: Fallbacks for new database functions
    try:
        from database import set_stop_scan_flag, should_stop_scan 
    except ImportError:
        def set_stop_scan_flag(stop_val): st.error("set_stop_scan_flag (fallback) not loaded.")
        def should_stop_scan(): st.error("should_stop_scan (fallback) not loaded."); return False

except ImportError as e:
    st.error(f"Critical Error: Failed to import core modules or paths: {e}. Application functionality will be severely limited.")
    # Define fallbacks for ALL imported names if an import fails
    if DB_PATH is None: # If utils.DB_PATH failed to import
        DB_PATH = Path(__file__).resolve().parent / "fallback_database.db" 
        st.warning(f"Using fallback database path: {DB_PATH}")

    # Fallback dummy functions if their imports failed
    if clear_all_approved_jobs is None:
        def clear_all_approved_jobs(): st.error("clear_all_approved_jobs (fallback) not loaded."); return 0
    if mark_job_as_applied is None:
        def mark_job_as_applied(pk): st.error("mark_job_as_applied (fallback) not loaded."); return False
    if delete_approved_job is None:
        def delete_approved_job(pk): st.error("delete_approved_job (fallback) not loaded."); return False
    if scrape_phase is None:
        def scrape_phase(): st.error("scrape_phase (fallback) not loaded."); return (0,0)
    # ADDED: Fallbacks for new database functions
    try:
        from database import set_stop_scan_flag, should_stop_scan 
    except ImportError:
        def set_stop_scan_flag(stop_val): st.error("set_stop_scan_flag (fallback) not loaded.")
        def should_stop_scan(): st.error("should_stop_scan (fallback) not loaded."); return False

# Call init_db() to ensure database and tables are created/updated
if DB_PATH: # Ensure DB_PATH is set before calling
    try:
        init_db() # Call init_db here
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
else:
    st.error("DB_PATH not configured. Database initialization skipped.")

# --- Database Schema Validation Function ---
def get_expected_db_schema():
    return {
        "discovered_jobs": {
            "id": {"type": "INTEGER", "notnull": 0, "pk": 1}, # type can be flexible, check for major ones
            "job_id": {"type": "INTEGER", "notnull": 1, "pk": 0}, # UNIQUE is not checked by PRAGMA table_info easily
            "url": {"type": "TEXT", "notnull": 1, "pk": 0},    # UNIQUE is not checked by PRAGMA table_info easily
            "title": {"type": "TEXT", "notnull": 0, "pk": 0},
            "description": {"type": "TEXT", "notnull": 0, "pk": 0},
            "location": {"type": "TEXT", "notnull": 0, "pk": 0},
            "keyword": {"type": "TEXT", "notnull": 0, "pk": 0},
            "date_discovered": {"type": "TIMESTAMP", "notnull": 0, "pk": 0}, # Often TEXT
            "analyzed": {"type": "BOOLEAN", "notnull": 0, "pk": 0} # Often INTEGER
        },
        "approved_jobs": {
            "id": {"type": "INTEGER", "notnull": 0, "pk": 1},
            "discovered_job_id": {"type": "INTEGER", "notnull": 1, "pk": 0}, # UNIQUE not checked easily
            "date_approved": {"type": "TIMESTAMP", "notnull": 0, "pk": 0},
            "reason": {"type": "TEXT", "notnull": 0, "pk": 0},
            "date_applied": {"type": "TIMESTAMP", "notnull": 0, "pk": 0},
            "is_archived": {"type": "BOOLEAN", "notnull": 0, "pk": 0}
        }
    }

def is_valid_database_schema(db_file_path: Path) -> tuple[bool, str]:
    expected_schema = get_expected_db_schema()
    try:
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()

        for table_name, expected_columns in expected_schema.items():
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            if not cursor.fetchone():
                conn.close()
                return False, f"Table '{table_name}' not found in the uploaded database."

            # Check columns
            cursor.execute(f"PRAGMA table_info('{table_name}');")
            actual_columns_info = {row[1]: {"type": str(row[2]).upper(), "notnull": row[3], "pk": row[5]} for row in cursor.fetchall()}
            
            for col_name, expected_attrs in expected_columns.items():
                if col_name not in actual_columns_info:
                    conn.close()
                    return False, f"Column '{col_name}' not found in table '{table_name}'."
                
                actual_attrs = actual_columns_info[col_name]
                
                # Type checking (flexible for SQLite's dynamic typing)
                # For TIMESTAMP and BOOLEAN, they might be stored as TEXT or INTEGER.
                # We mainly care if critical types like INTEGER for IDs are respected.
                # This is a simplified check; more robust type affinity checking could be added.
                if "INTEGER" in expected_attrs["type"] and "INT" not in actual_attrs["type"]:
                     pass # Allow for INT, INTEGER, BIGINT etc.
                elif expected_attrs["type"] != "TIMESTAMP" and expected_attrs["type"] != "BOOLEAN" and \
                     expected_attrs["type"] not in actual_attrs["type"]: # For TEXT, allow TEXT, VARCHAR etc.
                    # st.warning(f"Type mismatch for {table_name}.{col_name}: Expected containing '{expected_attrs['type']}', got '{actual_attrs['type']}'. Allowing due to SQLite flexibility.")
                    pass # Be lenient for now

                if expected_attrs["notnull"] != actual_attrs["notnull"]:
                    # conn.close() # Commenting out to allow minor schema diffs for now
                    # return False, f"NOT NULL constraint mismatch for column '{col_name}' in table '{table_name}'. Expected: {expected_attrs['notnull']}, Got: {actual_attrs['notnull']}"
                    st.warning(f"NOT NULL constraint mismatch for {table_name}.{col_name}. Expected: {expected_attrs['notnull']}, Got: {actual_attrs['notnull']}. Allowing.")


                if expected_attrs["pk"] != actual_attrs["pk"]:
                    conn.close()
                    return False, f"Primary Key constraint mismatch for column '{col_name}' in table '{table_name}'. Expected: {expected_attrs['pk']}, Got: {actual_attrs['pk']}"
            
            # Check if all actual columns are expected (no extra columns)
            # for actual_col_name in actual_columns_info.keys():
            #     if actual_col_name not in expected_columns:
            #         st.warning(f"Warning: Extra column '{actual_col_name}' found in table '{table_name}' in the uploaded database. Allowing.")


        conn.close()
        return True, "Database schema appears valid."
    except sqlite3.Error as e:
        return False, f"SQLite error during schema validation: {e}"
    except Exception as e:
        return False, f"Unexpected error during schema validation: {e}"


# 4. Now define functions that USE these global variables (like DB_PATH)
def fetch_approved_jobs():
    """Fetches all approved jobs, including their primary key and new date_applied status."""
    if not DB_PATH: # Check if DB_PATH was successfully initialized
        st.error("DB_PATH is not configured. Cannot fetch jobs.")
        return pd.DataFrame()
    if not DB_PATH.exists():
        st.error(f"Database file not found at: {DB_PATH}")
        return pd.DataFrame()

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        # Fetch aj.id AS approved_job_pk for button actions
        # Fetch aj.date_applied for display and button logic
        query = """
        SELECT
            aj.id AS approved_job_pk, 
            dj.url,
            dj.title,
            dj.location,
            dj.keyword,
            aj.date_approved,
            aj.reason,
            aj.date_applied 
        FROM
            approved_jobs aj
        JOIN
            discovered_jobs dj ON aj.discovered_job_id = dj.id
        WHERE aj.date_applied IS NULL  -- MODIFIED: Only fetch jobs not yet applied
        ORDER BY
            aj.date_approved DESC;
        """
        df = pd.read_sql_query(query, conn)
        
        if 'date_approved' in df.columns:
            try:
                df['date_approved'] = pd.to_datetime(df['date_approved']).dt.strftime('%Y-%m-%d %H:%M:%S')
            except: pass # Silently ignore formatting errors for date_approved
        if 'date_applied' in df.columns:
            try: # Format date_applied if it exists, but it can be None
                df['date_applied_str'] = pd.to_datetime(df['date_applied']).dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                df['date_applied_str'] = None # Keep as None if formatting fails or it's NaT
        else:
            df['date_applied_str'] = None # Ensure column exists even if all values are None

        return df
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

# Explicit session state initialization at the top
if 'scan_should_be_running' not in st.session_state:
    st.session_state.scan_should_be_running = False
if 'scan_actively_processing_in_this_run' not in st.session_state:
    st.session_state.scan_actively_processing_in_this_run = False
if 'user_requested_stop_in_this_run' not in st.session_state:
    st.session_state.user_requested_stop_in_this_run = False
if 'current_scan_stop_signal' not in st.session_state:
    st.session_state.current_scan_stop_signal = [False] # Default to a non-None list
if 'scan_message' not in st.session_state:
    st.session_state.scan_message = ""
if 'db_import_export_message' not in st.session_state:
    st.session_state.db_import_export_message = None # ADDED
if 'show_db_uploader' not in st.session_state: # ADDED
    st.session_state.show_db_uploader = False # ADDED
if 'action_message' not in st.session_state: # ADDED
    st.session_state.action_message = None # ADDED
# Assuming other session states like db_import_export_message, show_db_uploader, action_message are initialized elsewhere or as needed.

# --- Callback Functions for Sidebar Actions ---
def start_scan_action():
    if scrape_phase: # Ensure scrape_phase is loaded
        set_stop_scan_flag(False) # MODIFIED: Reset DB flag before starting
        st.session_state.scan_should_be_running = True
        st.session_state.scan_actively_processing_in_this_run = True
        st.session_state.user_requested_stop_in_this_run = False
        st.session_state.current_scan_stop_signal = [False] # Fresh signal for this new scan attempt
        st.session_state.scan_message = "Scan initiated..."
    else:
        st.session_state.scan_message = "ERROR: Scan function not available. Cannot start scan."
        st.session_state.scan_should_be_running = False 
        st.session_state.scan_actively_processing_in_this_run = False

def stop_scan_action():
    set_stop_scan_flag(True) # MODIFIED: Set DB flag to request stop
    st.session_state.scan_should_be_running = False  # User wants to stop the conceptual scan
    st.session_state.scan_actively_processing_in_this_run = False # Stop any processing in current run
    st.session_state.user_requested_stop_in_this_run = True       # Mark that stop was clicked for this interaction
    st.session_state.scan_message = "Scan stop requested. The scan will attempt to terminate if running. UI state reset."
    if st.session_state.current_scan_stop_signal:
        st.session_state.current_scan_stop_signal[0] = True # Attempt to signal current run's scrape_phase

def clear_jobs_action():
    global clear_all_approved_jobs 
    if clear_all_approved_jobs:
        try:
            deleted_count = clear_all_approved_jobs()
            st.session_state.scan_message = f"Successfully cleared {deleted_count} approved jobs."
        except Exception as e:
            st.session_state.scan_message = f"Error clearing approved jobs: {e}"
    else:
        st.session_state.scan_message = "ERROR: Clear jobs function not available."

# --- Global Actions (Sidebar) ---
st.sidebar.header("Job Management")
scan_status_placeholder = st.sidebar.empty()

# Update status placeholder based on current states
if st.session_state.get('scan_actively_processing_in_this_run', False):
    scan_status_placeholder.warning("Scan in progress... Please wait.")
elif st.session_state.get('scan_should_be_running', False): 
    scan_status_placeholder.info("A scan was previously initiated. It may be running (orphaned if page refreshed). Click 'Stop Scan' to reset UI state.")
elif st.session_state.get('user_requested_stop_in_this_run', False):
    scan_status_placeholder.info(st.session_state.scan_message or "Scan stop processed.") 
    st.session_state.user_requested_stop_in_this_run = False # Reset after displaying message
    st.session_state.scan_message = "" # Clear message
elif st.session_state.scan_message: # Residual messages
    scan_status_placeholder.info(st.session_state.scan_message)
    st.session_state.scan_message = ""
else:
    scan_status_placeholder.empty()

# Start Scan Button
st.sidebar.button("🚀 Start New Job Scan", 
    key="global_start_scan", 
    use_container_width=True, 
    # disabled=st.session_state.get('scan_should_be_running', False), # Disabled if a scan is conceptually running
    on_click=start_scan_action
)

# Stop Scan Button
st.sidebar.button("🛑 Stop Scan", 
    key="global_stop_scan", 
    use_container_width=True, 
    type="primary", 
    # disabled=(not st.session_state.get('scan_should_be_running', False)), # Enabled if a scan is conceptually running
    on_click=stop_scan_action
)

# Clear All Approved Jobs Button
st.sidebar.button("🗑️ Clear All Approved Jobs", 
    key="global_clear_approved", 
    use_container_width=True, 
    type="primary", 
    disabled=st.session_state.get('scan_should_be_running', False), # Disable if any scan is conceptually running
    on_click=clear_jobs_action
)

# --- Database Import/Export (Sidebar) ---
st.sidebar.markdown("---")
st.sidebar.subheader("Database Management")

# Display DB import/export message if it exists
if st.session_state.db_import_export_message:
    msg_type = st.session_state.db_import_export_message.get("type", "info")
    msg_text = st.session_state.db_import_export_message.get("text", "")
    if msg_type == "success":
        st.sidebar.success(msg_text)
    elif msg_type == "error":
        st.sidebar.error(msg_text)
    else:
        st.sidebar.info(msg_text)
    st.session_state.db_import_export_message = None # Clear after displaying

# Export Database Button
if DB_PATH and DB_PATH.exists():
    try:
        with open(DB_PATH, "rb") as fp:
            st.sidebar.download_button(
                label="📤 Export Database",
                data=fp,
                file_name="jobfinder_database.db",
                mime="application/vnd.sqlite3", # Standard mime type for SQLite
                use_container_width=True,
                help="Download the current application database."
            )
    except Exception as e:
        st.sidebar.error(f"Error preparing DB for export: {e}")
else:
    st.sidebar.download_button(
        label="📤 Export Database",
        data=b"", # Empty data
        file_name="jobfinder_database.db",
        mime="application/vnd.sqlite3",
        use_container_width=True,
        help="Database file not found or DB_PATH not set.",
        disabled=True
    )

# Import Database Button
if st.sidebar.button("📥 Import Database", use_container_width=True, key="show_db_uploader_button", help="Click to upload a database file. This will replace the current database if valid."):
    st.session_state.show_db_uploader = True

if st.session_state.show_db_uploader:
    uploaded_db_file = st.sidebar.file_uploader(
        "Upload database.db file",
        type=["db"],
        key="db_file_uploader_widget",
        label_visibility="collapsed"
    )

    if uploaded_db_file is not None:
        temp_dir = Path("temp_db_uploads")
        temp_dir.mkdir(exist_ok=True)
        temp_upload_path = temp_dir / uploaded_db_file.name

        try:
            with open(temp_upload_path, "wb") as f:
                f.write(uploaded_db_file.getvalue())
            
            is_valid, message = is_valid_database_schema(temp_upload_path)
            
            if is_valid:
                if DB_PATH:
                    shutil.move(temp_upload_path, DB_PATH) # Replace current DB
                    st.session_state.db_import_export_message = {"type": "success", "text": "Database imported successfully!"}
                     # Clear relevant caches or trigger re-initialization if needed
                    if load_main_config: load_main_config.cache_clear() # Example: clear config cache
                    # Potentially re-initialize parts of the app or just rerun
                else:
                    st.session_state.db_import_export_message = {"type": "error", "text": "DB_PATH not configured. Cannot save imported database."}
            else:
                st.session_state.db_import_export_message = {"type": "error", "text": f"Invalid DB schema: {message}"}
                if temp_upload_path.exists(): temp_upload_path.unlink() # Clean up invalid file

        except Exception as e:
            st.session_state.db_import_export_message = {"type": "error", "text": f"Error processing uploaded DB: {e}"}
            if temp_upload_path.exists(): temp_upload_path.unlink()
        finally:
            st.session_state.show_db_uploader = False
            if temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir) # Clean up temp directory
                except Exception as e_clean:
                    st.warning(f"Could not clean up temp_db_uploads: {e_clean}")
            st.rerun()

# --- Main Page Structure ---
st.title("📋 JobFinder - Approved Jobs Dashboard")
main_page_status_placeholder = st.empty() # Placeholder for spinner

# Conditional execution of the scan in the main page area, with a spinner
if st.session_state.get('scan_actively_processing_in_this_run', False):
    with main_page_status_placeholder.container(), st.spinner("🚀 Scanning for jobs... This may take a moment."):
        if load_main_config:
            try: load_main_config.cache_clear(); load_main_config();
            except Exception as e: st.warning(f"Could not clear/reload config: {e}")
        
        scan_outcome_message = ""
        natural_completion = False

        if scrape_phase and st.session_state.current_scan_stop_signal is not None:
            if not st.session_state.current_scan_stop_signal[0]: # If not already signaled to stop
                new_jobs, links_examined = scrape_phase(st.session_state.current_scan_stop_signal)
                if not st.session_state.current_scan_stop_signal[0]: # Check if scrape_phase was stopped by signal during its run
                    scan_outcome_message = f"Scan complete. New jobs: {new_jobs}. Links examined: {links_examined}."
                    natural_completion = True 
                # If current_scan_stop_signal[0] is True here, stop_scan_action already set the message.
            else: # Signal was true before calling scrape_phase
                scan_outcome_message = "Scan execution pre-empted by stop signal."
        elif not scrape_phase:
            scan_outcome_message = "Scan function not available. Scan aborted."
        else: # current_scan_stop_signal is None (should not happen with new init)
            scan_outcome_message = "Scan cannot start: stop signal not initialized properly."

        if scan_outcome_message: # Update session message only if not already set by stop_scan_action
             if not st.session_state.get('user_requested_stop_in_this_run', False):
                st.session_state.scan_message = scan_outcome_message
        
        if natural_completion: # If scan ran and completed without external stop signal this run
            st.session_state.scan_should_be_running = False
        
        st.session_state.scan_actively_processing_in_this_run = False # Always mark current run's processing as done
    
    main_page_status_placeholder.empty() 
    st.rerun()

# --- Display Approved Jobs ---
# Show jobs if not actively trying to scan in this run
if not st.session_state.get('scan_actively_processing_in_this_run', False):
    action_message_placeholder = st.empty() 
    if st.session_state.action_message:
        msg_type = st.session_state.action_message.get("type", "info")
        msg_text = st.session_state.action_message.get("text", "")
        if msg_type == "success":
            action_message_placeholder.success(msg_text)
        elif msg_type == "error":
            action_message_placeholder.error(msg_text)
        else:
            action_message_placeholder.info(msg_text)
        # Consider clearing the message after display if desired, e.g., by uncommenting:
        # st.session_state.action_message = {}


    approved_jobs_df = fetch_approved_jobs()

    if approved_jobs_df.empty:
        st.warning("No approved jobs found in the database. Click Start New Job Scan to begin.")
    else:
        st.metric(label="Total Approved Jobs", value=len(approved_jobs_df))
        # st.markdown("---") # Removed initial redundant separator here, separator will be after each card

        for index, row in approved_jobs_df.iterrows():
            with st.container(): # WRAP each job in a container
                approved_job_pk = row['approved_job_pk']
                title = html.escape(str(row['title'] if pd.notna(row['title']) else 'N/A'))
                url = str(row['url'] if pd.notna(row['url']) else '#')
                date_approved_val = row['date_approved']
                location_val = row.get('location', 'N/A')
                keyword_val = row.get('keyword', 'N/A')
                reason_val = html.escape(str(row.get('reason', 'N/A')))

                # Use two columns: one for details, one for actions
                col_details, col_actions = st.columns([5, 1.5]) # Adjusted column ratio

                with col_details:
                    # Make title larger and a styled link
                    st.markdown(f"<h5><a href='{url}' target='_blank' style='text-decoration: none; color: inherit !important;'>{title}</a></h5>", unsafe_allow_html=True)
                    
                    st.caption(f"📅 Approved: {date_approved_val} | 📍 Location: {location_val} | 🔑 Keyword: {keyword_val}")
                    
                    with st.expander("Reason for Approval"):
                        st.markdown(f"<div style='word-wrap: break-word; white-space: pre-wrap;'>{reason_val}</div>", unsafe_allow_html=True)

                with col_actions:
                    # ADDED: Attempt to add some vertical space to align buttons better
                    st.markdown("<br>", unsafe_allow_html=True) # Adjust <br> count or use specific margin if needed
                    # st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True) # Alternative spacing

                    applied_button_key = f"applied_{approved_job_pk}_{index}"
                    delete_button_key = f"delete_{approved_job_pk}_{index}"

                    if st.button("Mark as Applied", key=applied_button_key, 
                                  help="Mark this job as applied for.", 
                                  use_container_width=True):
                        if mark_job_as_applied(approved_job_pk):
                            st.session_state.action_message = {"type": "success", "text": f"Job '{title[:30]}...' marked as applied."}
                        st.rerun()
                    
                    # Add a little space between buttons if they are stacked vertically in the same column
                    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)

                    if st.button("Delete Job", key=delete_button_key, 
                                 help="Remove this job from the approved list.", 
                                 use_container_width=True, type="primary"):
                        if delete_approved_job(approved_job_pk):
                            st.session_state.action_message = {"type": "success", "text": f"Job '{title[:30]}...' deleted from approved list."}
                        else:
                            st.session_state.action_message = {"type": "error", "text": f"Failed to delete job '{title[:30]}...' (DB error or not found)."}
                        st.rerun()
            
            st.markdown("---") # Separator after each job card

