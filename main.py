# main.py
import database
import scrape
import sys
from evaluate import analyze_job

def _rowcount() -> int:
    with database.get_conn() as conn:
        return conn.execute("SELECT COUNT(*) FROM discovered_jobs").fetchone()[0]

def show_progress(idx: int, total: int, bar_len: int = 40) -> None:
    """Render a simple progress bar like  [██████------] 12/44 (27%)"""
    pct   = idx / total
    filled = int(bar_len * pct)
    bar   = "█" * filled + "-" * (bar_len - filled)
    sys.stdout.write(f"\r[{bar}] {idx}/{total} ({pct:.0%})")
    sys.stdout.flush()

def scrape_phase() -> None:
    start_total = _rowcount()

    searches = scrape.get_searches()
    total_searches = len(searches)

    processed = 0
    try:
        for i, search in enumerate(searches, 1):
            processed += scrape.process_search_page(search) or 0
            show_progress(i, total_searches)
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user – finishing up …")
    finally:
        end_total = _rowcount()
        print("\n──────────────── Summary ────────────────")
        print(f"Links examined    : {processed}")
        print(f"New jobs this run : {end_total - start_total}")
        print(f"Total in database : {end_total}")
        print("──────────────────────────────────────────")


def main() -> None:
    database.init_db()
    scrape_phase()


if __name__ == "__main__":
    main()
