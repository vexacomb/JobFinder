import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
import html
import time # For potential use with st.empty and messages

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

try:
    from utils import DB_PATH as UTILS_DB_PATH # Use an alias
    DB_PATH = UTILS_DB_PATH # Assign to the global DB_PATH

    from database import clear_all_approved_jobs as db_clear_approved
    clear_all_approved_jobs = db_clear_approved

    from database import mark_job_as_applied as db_mark_applied
    mark_job_as_applied = db_mark_applied

    from database import delete_approved_job as db_delete_approved
    delete_approved_job = db_delete_approved
    
    from scrape import scrape_phase as sp_scrape_phase
    scrape_phase = sp_scrape_phase

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

# Initialize session state
if 'scan_running' not in st.session_state:
    st.session_state.scan_running = False
if 'scan_message' not in st.session_state:
    st.session_state.scan_message = ""
if 'action_message' not in st.session_state: # For per-job action feedback
    st.session_state.action_message = {}

# --- Global Actions (Sidebar) ---
st.sidebar.header("Global Actions")
scan_status_placeholder = st.sidebar.empty()

if st.session_state.scan_running:
    scan_status_placeholder.warning("Scan in progress... Please wait.")
    st.sidebar.button("Start New Job Scan", disabled=True, key="global_start_scan")
    st.sidebar.button("Clear All Approved Jobs", disabled=True, key="global_clear_approved")
else:
    if st.session_state.scan_message: # Display global scan message
        scan_status_placeholder.info(st.session_state.scan_message)
        st.session_state.scan_message = "" 

    if st.sidebar.button("Start New Job Scan", key="global_start_scan"):
        if scrape_phase: # Check if function is available
            st.session_state.scan_running = True
            st.session_state.scan_message = "Scan initiated..."
            st.rerun() 
        else:
            st.error("Scan function not available due to import error.")

    if st.sidebar.button("Clear All Approved Jobs", key="global_clear_approved"):
        try:
            deleted_count = clear_all_approved_jobs()
            st.session_state.scan_message = f"Successfully cleared {deleted_count} approved jobs."
        except Exception as e:
            st.session_state.scan_message = f"Error clearing approved jobs: {e}"
        st.rerun() # MODIFIED from st.experimental_rerun()

if st.session_state.scan_running:
    scan_status_placeholder.warning("Scan in progress... Scraping and analyzing. See terminal for details.")
    new_jobs, links_examined = scrape_phase()
    st.session_state.scan_message = f"Scan complete. New jobs: {new_jobs}. Links examined: {links_examined}."
    st.session_state.scan_running = False
    st.rerun() # MODIFIED from st.experimental_rerun()

st.title("📋 JobFinder - Approved Jobs Dashboard")

# --- Display Approved Jobs ---

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
    st.warning("No approved jobs found in the database, or an error occurred fetching them.")
else:
    st.metric(label="Total Approved Jobs", value=len(approved_jobs_df))
    st.markdown("---")

    for index, row in approved_jobs_df.iterrows():
        approved_job_pk = row['approved_job_pk']
        title = html.escape(str(row['title'] if pd.notna(row['title']) else 'N/A'))
        url = str(row['url'] if pd.notna(row['url']) else '#')
        
        col1, col2, col3 = st.columns([4, 3, 2])

        with col1:
            st.markdown(f"**[{title}]({url})**")
            st.caption(f"Approved: {row['date_approved']} | Location: {row.get('location', 'N/A')} | Keyword: {row.get('keyword', 'N/A')}")
            
            # MODIFIED: Simplified is_applied logic
            is_applied = pd.notna(row['date_applied_str']) 

            if is_applied: # Check the boolean directly
                st.success(f"Applied on: {row['date_applied_str']}")
            else:
                st.info("Status: Not yet applied")

        with col2: 
            with st.expander("Reason for Approval"):
                st.markdown(f"<div style='word-wrap: break-word; white-space: pre-wrap;'>{html.escape(str(row.get('reason', 'N/A')))}</div>", unsafe_allow_html=True)
        
        with col3: 
            applied_button_key = f"applied_{approved_job_pk}_{index}"
            delete_button_key = f"delete_{approved_job_pk}_{index}"

            # is_applied (boolean) is used directly in 'disabled'
            if st.button("Mark as Applied", key=applied_button_key, disabled=is_applied, help="Mark this job as applied for." if not is_applied else "Already marked as applied."):
                if mark_job_as_applied(approved_job_pk):
                    st.session_state.action_message = {"type": "success", "text": f"Job '{title[:30]}...' marked as applied."}
                else:
                    st.session_state.action_message = {"type": "error", "text": f"Failed to mark '{title[:30]}...' as applied (possibly already marked or DB error)."}
                st.rerun() # MODIFIED from st.experimental_rerun()

            if st.button("Delete", key=delete_button_key, help="Remove this job from the approved list."):
                if delete_approved_job(approved_job_pk):
                    st.session_state.action_message = {"type": "success", "text": f"Job '{title[:30]}...' deleted from approved list."}
                else:
                    st.session_state.action_message = {"type": "error", "text": f"Failed to delete job '{title[:30]}...' (DB error or not found)."}
                st.rerun() # MODIFIED from st.experimental_rerun()
        st.markdown("---")

# --- Sidebar ---
st.sidebar.header("About JobFinder")
st.sidebar.info(
    """
    **JobFinder v0.2**

    This application helps automate finding and managing job postings.

    **Features:**
    * Scrapes LinkedIn for jobs.
    * Uses AI to evaluate job descriptions.
    * Stores and displays approved jobs.
    * Allows marking jobs as applied or deleting them.

    ---
    *Developed by Michael Busbee*
    """
)