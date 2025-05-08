import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path
import html # For escaping title text if it contains special HTML characters

# Attempt to import DB_PATH from your existing database module
try:
    from database import DB_PATH
except ImportError:
    # Fallback logic
    print("Warning: Could not import DB_PATH from database.py. Using default 'database.db' relative to this script.")
    DB_PATH = Path(__file__).resolve().parent / "database.db"


def fetch_approved_jobs():
    """Fetches all approved jobs from the database and returns them as a DataFrame."""
    if not DB_PATH.exists():
        st.error(f"Database file not found at: {DB_PATH}")
        return pd.DataFrame()

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
        SELECT
            dj.url,
            dj.title,
            dj.location,
            dj.keyword,
            aj.date_approved,
            aj.reason
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
            except Exception as e:
                st.warning(f"Could not format 'date_approved': {e}")
        return df
    except sqlite3.Error as e:
        st.error(f"SQLite error: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.close()

# --- Streamlit App Layout ---
st.set_page_config(page_title="JobFinder Approved Jobs", layout="wide")

st.title("JobFinder - Approved Job Postings")

st.markdown("""
This dashboard displays jobs that have been scraped, analyzed by AI, and marked as 'approved'.
""")

approved_jobs_df = fetch_approved_jobs()

if approved_jobs_df.empty:
    st.warning("No approved jobs found in the database yet, or an error occurred fetching them.")
else:
    st.subheader("Approved Jobs List")

    # Make a copy to avoid SettingWithCopyWarning when creating the link column
    display_df = approved_jobs_df.copy()

    # Ensure 'title' and 'url' are strings, handle None values, and escape title for HTML
    display_df['title_escaped'] = display_df['title'].fillna('N/A').apply(html.escape)
    display_df['url_filled'] = display_df['url'].fillna('#')
    
    # Create the HTML link column
    display_df["Job Title"] = display_df.apply(
        lambda row: f'<a href="{row["url_filled"]}" target="_blank">{row["title_escaped"]}</a>', 
        axis=1
    )

    # Define the columns to display and their order
    # We use "Job Title" (our HTML link column) and not the original 'title' or 'url_filled', 'title_escaped'
    final_columns_in_order = ["date_approved", "Job Title", "location", "keyword", "reason"]
    
    # Select only the columns we want to display, in the desired order
    df_to_render = display_df[final_columns_in_order]

    # Convert the DataFrame to HTML, ensuring 'escape=False' to render our <a> tags
    # and 'index=False' to hide the DataFrame index.
    html_table = df_to_render.to_html(escape=False, index=False)

    # Use st.markdown to render the HTML table.
    # Word wrapping for the 'reason' column will be handled by the browser.
    st.markdown(html_table, unsafe_allow_html=True)

    st.metric(label="Total Approved Jobs", value=len(approved_jobs_df))

st.sidebar.header("About")
st.sidebar.info(
    "This dashboard is part of the JobFinder application. "
    "It reads from the `approved_jobs` table in the `database.db` SQLite database."
)