import database
import scrape


def main():
    database.init_db()
    jobs = scrape.get_jobs()

    # Counters
    total_jobs = len(jobs)

    for job in jobs:
        job_data = scrape.get_job_data(job)
        database.upsert_discovered(job_data)
        

    print("Total jobs: ", total_jobs)

if __name__ == "__main__":
    main()
