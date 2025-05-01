import requests
from bs4 import BeautifulSoup
import evaluate


locations = [
    "remote",  
    "Winchester, Virginia, United States",
    "Augusta, Georgia, United States"  
]

keywords = [
"Security Operations Center Analyst"
]


def search():
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

def get_soup(url):
    HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }

    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        return BeautifulSoup(resp.text, 'html.parser')
    return None

def extract_job_urls(soups):
    """Return unique LinkedIn job‐posting URLs.
    The argument can be either:
    • a single BeautifulSoup object, or
    • an iterable (list / tuple / set) of BeautifulSoup objects.
    """
    
    if soups is None:
        return []

    # Normalize to an iterable of soups
    if hasattr(soups, "find_all"):
        soups = [soups]

    job_urls = set()
    for soup in soups:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/jobs/view/" in href:
                if href.startswith("/"):
                    href = "https://www.linkedin.com" + href
                job_urls.add(href)

    return list(job_urls)

def extract_job_description(job_soup):
    """Extract job description using multiple possible selectors"""
    description = None
    
    # List of possible selectors for job descriptions
    description_selectors = [
        ('div', {'class_': 'description__text'}),
        ('div', {'class_': 'show-more-less-html__markup'}),
        ('div', {'class_': 'job-description'}),
        ('div', {'class_': 'jobs-description__content'}),
        ('div', {'class_': 'jobs-box__html-content'}),
        ('section', {'class_': 'description'}),
        ('div', {'class_': 'jobs-description'}),
        ('div', {'class_': 'jobs-unified-description__content'}),
        ('div', {'class_': 'jobs-description-content'}),
        ('div', {'id': 'job-details'}),
        ('div', {'class_': lambda x: x and 'description' in x.lower() if x else False}),
        ('div', {'class_': lambda x: x and 'job-details' in x.lower() if x else False})
    ]
    
    for tag, attrs in description_selectors:
        element = job_soup.find(tag, attrs)
        if element:
            description = element.get_text(separator=' ', strip=True)
            if description:
                return description
            
            description = ' '.join([p.get_text(strip=True) for p in element.find_all(['p', 'li'])])
            if description:
                return description
    
    job_details = job_soup.find_all(['div', 'section'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['job', 'description', 'details']) if x else False)
    for element in job_details:
        description = element.get_text(separator=' ', strip=True)
        if description and len(description) > 100:
            return description

def extract_job_title(job_soup):
    """Try several possible selectors / patterns to obtain the job title text from a LinkedIn job page."""
    # common places the title shows up on a full job page
    title_selectors = [
        ('h1', {'class_': 'topcard__title'}),
        ('h1', {'class_': 'jobs-unified-top-card__job-title'}),
        ('h1', {'class_': 'jobs-details-top-card__job-title'}),
        ('h1', {}),                       # plain first H1
        ('h2', {'class_': 'topcard__title'}),
        ('h2', {'class_': 't-24'}),       # generic large heading
        ('div', {'class_': 'job-title'}),
        ('span', {'class_': 'job-title'}),
    ]

    for tag, attrs in title_selectors:
        element = job_soup.find(tag, attrs)
        if element:
            title = element.get_text(strip=True)
            if title:
                return title

    # Fallback: meta og:title – often contains e.g. "Job Title – Company | LinkedIn"
    og_title = job_soup.find('meta', property='og:title')
    if og_title and og_title.get('content'):
        return og_title['content'].split('|')[0].strip()

    return None

def get_jobs():
    search_urls = search()
    job_urls = []
    for url in search_urls:
        soup = get_soup(url)
        job_urls = extract_job_urls(soup)


    seen = set()
    unique_urls = []

    for url in job_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    return unique_urls

def get_job_data(urls):

    for url in urls:
        job_soup = get_soup(url)
        title = extract_job_title(job_soup)

        if evaluate.contains_exclusions(title):
            continue
        description = extract_job_description(job_soup)
        print(title)
        print(description)
        print(url, "\n")
