import database
import scrape
import evaluate

def main():
    # database.create_table()
    jobs = scrape.get_jobs()

    # Counters
    total_jobs = len(jobs)
    failed_to_fetch = 0
    failed_to_extract_title = 0
    failed_on_exclusion_keyword = 0

    for job in jobs:
        job_data = scrape.get_job_data(job["url"])
        if job_data is None:
            failed_to_fetch += 1
            continue
        
        if job_data["failed_to_fetch"]:
            failed_to_fetch += 1
        elif job_data["failed_to_extract_title"]:
            failed_to_extract_title += 1
        elif job_data["failed_on_exclusion_keyword"]:
            failed_on_exclusion_keyword += 1


    print("Total jobs: ", total_jobs)
    print("Failed to fetch: ", failed_to_fetch)
    print("Failed to extract title: ", failed_to_extract_title)
    print("Failed on exclusion keyword: ", failed_on_exclusion_keyword)

if __name__ == "__main__":
    main()
