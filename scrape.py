import requests
from bs4 import BeautifulSoup
import evaluate
import json, html, re

locations = [
    "remote",  
    "Winchester, Virginia, United States",
    # "Augusta, Georgia, United States"  
]

keywords = [
    "Security Operations Center Analyst",
    "SOC Analyst",
    "Security Analyst"
]


def get_searches():
    searches = []

    for location in locations:
        for keyword in keywords:
            
            if location.lower() == "remote":
                # Search for remote positions
                url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&f_WT=2"
                searches.append({"url": url, "location": location, "keyword": keyword})
            else:
                url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}&distance=75&f_WT=1"
                searches.append({"url": url, "location": location, "keyword": keyword})
                url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}&distance=75&f_WT=3"
                searches.append({"url": url, "location": location, "keyword": keyword})

    return searches

def get_soup(url):
    HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    }
    soup = None
    resp = requests.get(url, headers=HEADERS)
    if resp.status_code == 200:
        soup =  BeautifulSoup(resp.text, 'html.parser')
    return soup

def extract_job_urls(soups):
    if soups is None:
        return []
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

def strip_html_tags(raw: str) -> str:
    return BeautifulSoup(raw, "html.parser").get_text(" ", strip=True)

def clean_description(raw_html: str) -> str:

    # First, decode HTML entities
    decoded = html.unescape(raw_html)
    
    # Remove nested tags, keeping their text content
    def strip_tags(text):
        return re.sub('<[^<]+?>', '', text)
    
    # Remove all HTML tags
    no_tags = strip_tags(decoded)
    
    # Replace multiple newlines/spaces with single space
    cleaned = re.sub(r'\s+', ' ', no_tags)
    
    # Optional: Convert list-like structures to more readable format
    cleaned = re.sub(r'\s*•\s*', '\n• ', cleaned)
    cleaned = re.sub(r'\s*-\s*', '\n- ', cleaned)
    
    # Remove common LinkedIn boilerplate
    boilerplate_patterns = [
        r'Pay Range:.*',
        r'The specific compensation.*',
        r'Full job description.*',
        r'About the job.*'
    ]
    for pattern in boilerplate_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    return cleaned.strip()

def extract_job_description(job_soup):
    # 1) look for ld+json
    for script in job_soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
        except Exception:
            continue
        if isinstance(data, dict) and "description" in data:
            return clean_description(data["description"])

    # 2) fallback to decoratedJobPosting = {...};
    pattern = re.compile(r"decoratedJobPosting\":({.*?})},\"applyMethod",
                         re.DOTALL)
    m = pattern.search(job_soup.text)
    if m:
        data = json.loads(m.group(1))
        if "description" in data:
            return clean_description(data["description"])

    # 3) last-chance: try the old div selectors (for logged-in HTML)
    container = job_soup.find(id="job-details") or \
                job_soup.find("div",
                    class_=lambda c: c and "jobs-description__content" in c)
    if container:
        return clean_description(container.decode_contents())

    return None

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
    searches = get_searches()
    jobs = []
    for search  in searches:
        url = search["url"]
        location = search["location"]
        keyword = search["keyword"]
        soup = get_soup(url)
        job_urls = extract_job_urls(soup)
        for url in job_urls:
            jobs.append({"url": url, "location": location, "keyword": keyword})
        #job_urls.extend(extract_job_urls(soup))


    seen = set()
    unique_jobs = []

    for job in jobs:
        if job["url"] not in seen:
            seen.add(job["url"])
            unique_jobs.append(job)
    return unique_jobs

def get_job_data(url):
    job_soup = get_soup(url)
    location = ""
    keyword = ""
    title = ""
    description = ""
    failed_to_fetch = False
    failed_to_extract_title = False
    failed_on_exclusion_keyword = False

    job_data = {
        "url": url,
        "location": location,
        "keyword": keyword,
        "title": title,
        "description": description,
        "failed_to_fetch": failed_to_fetch,
        "failed_to_extract_title": failed_to_extract_title,
        "failed_on_exclusion_keyword": failed_on_exclusion_keyword
    }

    if job_soup is None:
        failed_to_fetch = True
    else:
        title = extract_job_title(job_soup)
        if title is None:
            failed_to_extract_title = True
            return job_data
        failed_on_exclusion_keyword = evaluate.contains_exclusions(title)
        description = extract_job_description(job_soup)
        return job_data

