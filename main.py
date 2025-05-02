import database
import scrape

def main():
    # database.create_table()
    job_urls = scrape.get_jobs()
    total_jobs = len(job_urls)
    print(total_jobs)
"""    for url in job_urls:
        scrape.get_job_data(url)"""

if __name__ == "__main__":
    main()
