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
    date_discovered TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

DDL_APPROVED = """
CREATE TABLE IF NOT EXISTS approved_jobs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    discovered_job_id INTEGER UNIQUE NOT NULL,
    date_approved     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(discovered_job_id)
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
        (job_id, url, title, description, location, keyword)
    VALUES
        (:job_id, :url, :title, :description, :location, :keyword)
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
            "INSERT OR IGNORE INTO approved_jobs (discovered_job_id) VALUES (?);",
            (row["id"],),
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