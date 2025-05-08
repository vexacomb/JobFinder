# database.py

from pathlib import Path
import sqlite3
from contextlib import contextmanager
from typing import Iterable, Dict, Any
from scrape import _JOB_ID_RE

# -- DB location -------------------------------------------------------------
DB_PATH = Path(__file__).with_suffix(".db")  # <project>/jobfinder.db


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
    FOREIGN KEY (discovered_job_id)
        REFERENCES discovered_jobs(id) ON DELETE CASCADE
);
"""



def init_db() -> None:
    """Create the database file and tables if they do not exist."""
    with get_conn() as conn:
        conn.executescript(DDL_DISCOVERED + DDL_APPROVED)


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


def approve_job(url: str) -> bool:
    """Mark a job as approved by URL.  
    Returns True on success, False if the URL was not found.
    """
    with get_conn() as conn:
        cur = conn.execute("SELECT id FROM discovered_jobs WHERE url = ?;", (url,))
        row = cur.fetchone()
        if not row:
            return False
        conn.execute(
            "INSERT OR IGNORE INTO approved_jobs (discovered_job_id, reason) VALUES (?, ?);",
            (row["id"], row["reason"]),
        )
        return True


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
