import database
import scrape

def main():
    # database.create_table()
    urls = scrape.get_jobs()
    scrape.get_job_data(urls)

if __name__ == "__main__":
    main()
