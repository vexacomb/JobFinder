import database
import scrape


def main():
    # database.create_table()
    jobs = scrape.get_jobs()

    # Counters
    total_jobs = len(jobs)

    for job in jobs:
        job_data = scrape.get_job_data(job)
        

    print("Total jobs: ", total_jobs)

if __name__ == "__main__":
    main()
