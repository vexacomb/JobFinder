# main.py
import database
import scrape
import sys
from evaluate import analyse_job

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

def evaluate_phase(limit: int | None = None) -> None:
    from database import get_conn
    with get_conn() as conn:
        cur = conn.execute("SELECT id, url, COALESCE(description,'') AS description FROM discovered_jobs")
        for idx, row in enumerate(cur, 1):
            if limit and idx > limit:
                break
            if not row["description"].strip():       # skip blank descriptions
                continue
            res_openai  = analyse_job(row["description"], provider="openai",  temperature=0)
            res_gemini  = analyse_job(row["description"], provider="gemini", temperature=0)
            if res_openai["eligible"] != res_gemini["eligible"]:
                print(f"{row['id']} {row['url']}\n  openai: {res_openai['eligible']}  gemini: {res_gemini['eligible']}\n")
                print(f"OpenAI:\n\n{res_openai['reasoning']}\n\nGemini:\n\n{res_gemini['reasoning']}\n")


def main() -> None:
    database.init_db()
    # scrape_phase()
    evaluate_phase(limit=10)

if __name__ == "__main__":
    main()
