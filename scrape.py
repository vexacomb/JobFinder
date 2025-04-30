import requests
from bs4 import BeautifulSoup
import re

def search():
    locations = [
        "remote",  
        "Winchester, Virginia, United States",
        "Augusta, Georgia, United States"  
    ]

    keywords = [
    "Security Operations Center Analyst"
    ]

    urls = []

    for location in locations:
        for keyword in keywords:
            if location.lower() == "remote":
                # Search for remote positions
                url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&f_WT=2"
                urls.append(url)
            else:
                url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}&distance=75&f_WT=1"
                urls.append(url)
                url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}&distance=75&f_WT=3"
                urls.append(url)

    return urls

def scan(urls):
    HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }
    soups = []
    for url in urls:
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code == 200:
            soups.append(BeautifulSoup(resp.text, 'html.parser'))
    return soups

def extract_job_links(soups):
    job_links = set()
    for soup in soups:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/jobs/view/" in href:
                # make it absolute
                if href.startswith("/"):
                    href = "https://www.linkedin.com" + href
                job_links.add(href)

    return list(job_links)

def get_urls():
    urls = search()
    soups = scan(urls)
    job_links = extract_job_links(soups)
    return job_links

if __name__ == "__main__":
    for url in get_urls():
        print(url)
