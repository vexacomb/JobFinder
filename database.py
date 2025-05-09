# database.py

from pathlib import Path
import sqlite3
from contextlib import contextmanager
from typing import Iterable, Dict, Any, Optional, Tuple, List
from scrape import _JOB_ID_RE
from utils import DB_PATH

# -- DB location -------------------------------------------------------------


# -- connection helpers ------------------------------------------------------
@contextmanager
def get_conn():
    """Context‑managed connection that commits on success and rolls back on error."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row       # fetch rows as dict‑like objects
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# -- schema ------------------------------------------------------------------
DDL_DISCOVERED = """
CREATE TABLE IF NOT EXISTS discovered_jobs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id          INTEGER UNIQUE NOT NULL,
    url             TEXT UNIQUE NOT NULL,
    title           TEXT,
    description     TEXT,
    location        TEXT,
    keyword         TEXT,
    date_discovered TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analyzed        BOOLEAN DEFAULT FALSE
);
"""

DDL_APPROVED = """
CREATE TABLE IF NOT EXISTS approved_jobs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    discovered_job_id INTEGER UNIQUE NOT NULL,
    date_approved     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason            TEXT,
    date_applied      TIMESTAMP NULL, -- Added new column, allow NULL
    is_archived       BOOLEAN DEFAULT FALSE, -- Added for archiving
    FOREIGN KEY (discovered_job_id)
        REFERENCES discovered_jobs(id) ON DELETE CASCADE
);
"""



def init_db() -> None:
    """Create the database file and tables if they do not exist.
    Also attempts to add new columns to existing tables if they are missing.
    """
    with get_conn() as conn:
        conn.executescript(DDL_DISCOVERED) # Create discovered_jobs first
        conn.executescript(DDL_APPROVED)   # Create approved_jobs

        # Attempt to add the date_applied column to approved_jobs if it doesn't exist
        try:
            cursor = conn.execute("PRAGMA table_info(approved_jobs);")
            columns = [row['name'] for row in cursor.fetchall()]
            if 'date_applied' not in columns:
                conn.execute("ALTER TABLE approved_jobs ADD COLUMN date_applied TIMESTAMP NULL;")
                print("Added 'date_applied' column to 'approved_jobs' table.")
            if 'is_archived' not in columns: # Check and add is_archived
                conn.execute("ALTER TABLE approved_jobs ADD COLUMN is_archived BOOLEAN DEFAULT FALSE;")
                print("Added 'is_archived' column to 'approved_jobs' table.")
        except sqlite3.Error as e:
            print(f"Notice: Could not add new columns to 'approved_jobs' (may already exist or other issue): {e}")


# -- CRUD helpers ------------------------------------------------------------
def upsert_discovered(job: Dict[str, Any]) -> None:
    """Insert a job if it is new; ignore duplicates (thanks to UNIQUE on url)."""
    sql = """
    INSERT INTO discovered_jobs
        (job_id, url, title, description, location, keyword, analyzed)
    VALUES
        (:job_id, :url, :title, :description, :location, :keyword, :analyzed)
    ON CONFLICT(job_id) DO NOTHING;
    """
    job["job_id"] = int(_JOB_ID_RE.search(job["url"]).group(1))
    with get_conn() as conn:
        conn.execute(sql, job)


def approve_job(linkedin_job_id: int, reason: str) -> bool:
    """Mark a job as approved by its LinkedIn job_id.
    Inserts into approved_jobs if the job is found in discovered_jobs and not already approved.
    Returns True if a new row was inserted into approved_jobs, False otherwise.
    """
    with get_conn() as conn:
        # First, get the discovered_jobs.id (PK) using the linkedin_job_id
        cur_select = conn.execute("SELECT id FROM discovered_jobs WHERE job_id = ?;", (linkedin_job_id,))
        row = cur_select.fetchone()

        if not row:
            # No job found in discovered_jobs with this LinkedIn job_id
            return False

        discovered_job_row_id = row["id"]

        # Now insert into approved_jobs
        sql_insert = """
        INSERT INTO approved_jobs (discovered_job_id, reason)
        VALUES (?, ?)
        ON CONFLICT(discovered_job_id) DO NOTHING;
        """
        cur_insert = conn.execute(sql_insert, (discovered_job_row_id, reason))
        return cur_insert.rowcount == 1


def fetch_unapproved() -> Iterable[sqlite3.Row]:
    """Iterate over jobs that have not yet been approved."""
    sql = """
    SELECT d.*
    FROM discovered_jobs AS d
    LEFT JOIN approved_jobs AS a
      ON d.id = a.discovered_job_id
    WHERE a.id IS NULL
    ORDER BY date_discovered DESC;
    """
    with get_conn() as conn:
        yield from conn.execute(sql)

def insert_stub(job_id: int, url: str, location: str, keyword: str) -> bool:
    """
    Try to create a row with just the identifiers.
    Returns True if a new row was inserted, False if it already existed.
    """
    sql = """
    INSERT INTO discovered_jobs (job_id, url, location, keyword, analyzed)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(job_id) DO NOTHING;
    """
    with get_conn() as conn:
        cur = conn.execute(sql, (job_id, url, location, keyword, False))
        return cur.rowcount == 1        # 1 == new row, 0 == duplicate

def row_missing_details(job_id: int) -> bool:
    sql = """
    SELECT 1
      FROM discovered_jobs
     WHERE job_id = ?
       AND (title IS NULL OR title = '' OR description IS NULL OR description = '')
       AND analyzed = FALSE
     LIMIT 1;
    """
    with get_conn() as conn:
        return conn.execute(sql, (job_id,)).fetchone() is not None


def update_details(job_id: int, title: str | None, desc: str | None) -> None:
    sql = """
    UPDATE discovered_jobs
       SET title       = COALESCE(?, title),
           description = COALESCE(?, description)
     WHERE job_id = ?;
    """
    with get_conn() as conn:
        conn.execute(sql, (title, desc, job_id))

def mark_job_as_analyzed(job_id: int) -> None:
    """Mark a job as analyzed in the discovered_jobs table."""
    sql = """
    UPDATE discovered_jobs
       SET analyzed = TRUE
     WHERE job_id = ?;
    """
    with get_conn() as conn:
        conn.execute(sql, (job_id,))

def clear_all_approved_jobs() -> int:
    """Deletes all records from the approved_jobs table.
    Returns the number of rows deleted.
    """
    sql = "DELETE FROM approved_jobs;"
    with get_conn() as conn:
        cur = conn.execute(sql)
        return cur.rowcount
    
def mark_job_as_applied(approved_job_pk: int) -> bool:
    """Marks a specific job in approved_jobs as applied by setting the date_applied.
    Uses the primary key (id) of the approved_jobs table.
    Returns True if the update was successful and a row was affected, False otherwise.
    """
    sql = """
    UPDATE approved_jobs
    SET date_applied = CURRENT_TIMESTAMP
    WHERE id = ? AND date_applied IS NULL; -- Only update if not already applied
    """
    with get_conn() as conn:
        cur = conn.execute(sql, (approved_job_pk,))
        return cur.rowcount > 0 # rowcount is 1 if updated, 0 if already applied or not found

def delete_approved_job(approved_job_pk: int) -> bool:
    """Deletes a specific job from the approved_jobs table.
    Uses the primary key (id) of the approved_jobs table.
    Returns True if a row was deleted, False otherwise.
    """
    sql = "DELETE FROM approved_jobs WHERE id = ?;"
    with get_conn() as conn:
        cur = conn.execute(sql, (approved_job_pk,))
        return cur.rowcount > 0

def archive_all_applied_jobs() -> int:
    """Marks all applied jobs as archived.
    Sets is_archived = TRUE for jobs where date_applied is not NULL and is_archived is FALSE.
    Returns the number of rows updated.
    """
    sql = """
    UPDATE approved_jobs
    SET is_archived = TRUE
    WHERE date_applied IS NOT NULL AND (is_archived = FALSE OR is_archived IS NULL);
    """
    with get_conn() as conn:
        cur = conn.execute(sql)
        return cur.rowcount