import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path
from utils import DB_PATH # Assuming DB_PATH is correctly defined in utils
import altair as alt # ADDED Altair for better charts

# --- Page Config ---
st.set_page_config(
    page_title="JobFinder - Statistics",
    layout="wide"
)

# --- Helper Functions ---
@st.cache_resource # MODIFIED: Changed from st.cache_data to st.cache_resource
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    if not DB_PATH:
        st.error("Database path (DB_PATH) is not configured in utils.py.")
        return None
    if not Path(DB_PATH).exists():
        st.error(f"Database file not found at: {DB_PATH}")
        return None
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except sqlite3.Error as e:
        st.error(f"SQLite error connecting to database: {e}")
        return None

@st.cache_data # Cache the data loading and processing
def fetch_job_data_for_stats():
    """Fetches all necessary data from discovered_jobs and approved_jobs."""
    conn = get_db_connection()
    if conn is None:
        return pd.DataFrame(), pd.DataFrame()

    try:
        discovered_df = pd.read_sql_query("SELECT * FROM discovered_jobs", conn)
        approved_df = pd.read_sql_query("""
            SELECT aj.*, dj.keyword, dj.location, dj.title as discovered_title
            FROM approved_jobs aj
            JOIN discovered_jobs dj ON aj.discovered_job_id = dj.id
        """, conn)
        conn.close()
        return discovered_df, approved_df
    except pd.errors.DatabaseError as e: # More specific exception for pandas SQL errors
        st.error(f"Error fetching data for statistics: {e}")
        if conn: conn.close() # Ensure connection is closed on error
        return pd.DataFrame(), pd.DataFrame()
    except Exception as e: # Catch any other unexpected errors
        st.error(f"An unexpected error occurred while fetching statistics data: {e}")
        if conn: conn.close()
        return pd.DataFrame(), pd.DataFrame()

# --- Main Page ---
st.title("📊 Job Application Statistics")
st.markdown("Insights into your job discovery and approval process.")

discovered_jobs_df, approved_jobs_df = fetch_job_data_for_stats()

if discovered_jobs_df.empty and approved_jobs_df.empty and Path(DB_PATH).exists():
    st.warning("No data found in the database. Start a scan or approve some jobs to see statistics.")
elif not Path(DB_PATH).exists():
    # Error already shown by get_db_connection, but an additional page-level message can be useful
    pass # Avoid redundant error messages if DB_PATH is invalid
else:
    # --- Overall Job Funnel Metrics ---
    st.header("🚀 Overall Job Funnel")
    total_discovered = len(discovered_jobs_df)
    total_analyzed = len(discovered_jobs_df[discovered_jobs_df['analyzed'] == True]) # SQLite stores booleans as 0 or 1
    total_approved = len(approved_jobs_df)
    total_applied = len(approved_jobs_df[approved_jobs_df['date_applied'].notna()])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Discovered Jobs", total_discovered)
    col2.metric("Jobs Analyzed", total_analyzed)
    col3.metric("Jobs Approved", total_approved)
    col4.metric("Jobs Applied", total_applied)

    st.markdown("---")

    # --- Approved Jobs by Keyword ---
    st.header("🔑 Approved Jobs by Keyword")
    if not approved_jobs_df.empty and 'keyword' in approved_jobs_df.columns:
        keyword_counts_df = approved_jobs_df['keyword'].value_counts().reset_index()
        keyword_counts_df.columns = ['keyword', 'count']
        keyword_counts_df = keyword_counts_df.sort_values(by='count', ascending=False)
        
        if not keyword_counts_df.empty:
            chart = alt.Chart(keyword_counts_df).mark_bar().encode(
                x=alt.X('count:Q', title='Number of Approved Jobs'),
                y=alt.Y('keyword:N', title='Keyword', sort='-x') # Sorts by count descending on y-axis
            ).properties(
                # title='Approved Jobs by Keyword' # Title can be handled by st.header
            )
            st.altair_chart(chart, use_container_width=True)
            # st.bar_chart(keyword_counts) # REPLACED with Altair chart
        else:
            st.info("No approved jobs with keyword data found.")
    elif approved_jobs_df.empty:
        st.info("No approved jobs yet to analyze by keyword.")
    else:
        st.warning("Keyword data is missing from approved jobs.")
    
    st.markdown("---")

    # --- Approved Jobs by Location ---
    st.header("📍 Approved Jobs by Location")
    if not approved_jobs_df.empty and 'location' in approved_jobs_df.columns:
        location_counts_df = approved_jobs_df['location'].value_counts().reset_index()
        location_counts_df.columns = ['location', 'count']
        location_counts_df = location_counts_df.sort_values(by='count', ascending=False)

        if not location_counts_df.empty:
            chart = alt.Chart(location_counts_df).mark_bar().encode(
                x=alt.X('count:Q', title='Number of Approved Jobs'),
                y=alt.Y('location:N', title='Location', sort='-x') # Sorts by count descending on y-axis
            ).properties(
                # title='Approved Jobs by Location' # Title can be handled by st.header
            )
            st.altair_chart(chart, use_container_width=True)
            # st.bar_chart(location_counts) # REPLACED with Altair chart
        else:
            st.info("No approved jobs with location data found.")
    elif approved_jobs_df.empty:
        st.info("No approved jobs yet to analyze by location.")
    else:
        st.warning("Location data is missing from approved jobs.")

    # --- Placeholder for more stats ---
    # st.markdown("---")
    # st.header("Further Analysis (Coming Soon)")
    # st.info("More detailed statistics and visualizations will be added here.")

# Fallback message if DB_PATH itself is the issue (handled by get_db_connection implicitly)
# but an explicit check at the end might be good if all dataframes are empty for other reasons
if not DB_PATH or not Path(DB_PATH).exists():
    st.error("Database not found. Please ensure the application is set up correctly and a database exists.") 