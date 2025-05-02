import database
import scrape


def main():
    database.init_db()

    with database.get_conn() as conn:
        starting_total = conn.execute("SELECT COUNT(*) FROM discovered_jobs").fetchone()[0]
    print(f"Discovered jobs in DB: {starting_total}")    
    for search in scrape.get_searches():
        scrape.process_search_page(search)
    
    with database.get_conn() as conn:
        ending_total = conn.execute("SELECT COUNT(*) FROM discovered_jobs").fetchone()[0]
    
    print(f"New jobs: {ending_total - starting_total}")

if __name__ == "__main__":
    main()
