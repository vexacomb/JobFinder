import requests
from bs4 import BeautifulSoup
import evaluate
import json, html, re, urllib
from urllib.parse import urlparse, parse_qs
from config import load
import database
import random
from typing import Sequence, List, TypeVar

T = TypeVar("T")

config = load()
locations = config["locations"]
keywords = config["keywords"]



_JOB_ID_RE = re.compile(r"/jobs/view/(?:[^/?]*-)?(\d+)(?:[/?]|$)")

def shuffled(seq: Sequence[T]) -> List[T]:
    """Return a new list containing all items from *seq* in random order."""
    tmp = list(seq)          # copy so the caller’s list is untouched
    random.shuffle(tmp)
    return tmp

def process_search_page(search):
    """Visit one LinkedIn search URL and stream rows into the DB."""

    handled = 0
    soup = get_soup(search["url"])
    if soup is None:
        return 0

    
    for a in soup.find_all("a", href=True):
        text = a.get_text(" ", strip=True)
        if evaluate.contains_exclusions(text):
            continue

        href = a["href"]
        if "/jobs/view/" not in href:
            continue

        full  = "https://www.linkedin.com" + href if href.startswith("/") else href
        url   = canonical_job_url(full)
        job_id = extract_job_id(url)
        if job_id is None:
            continue      # can’t index it

        # ---- 1) quick INSERT; skip rest of loop if already seen ----------
        if not database.insert_stub(job_id, url, search["location"], search["keyword"]):
            continue

        # ---- 2) only NEW postings reach this point -----------------------
        job_soup = get_soup(url)
        title = extract_job_title(job_soup) if job_soup else None
        desc  = extract_job_description(job_soup) if job_soup else None
        database.update_details(job_id, title, desc)
        handled += 1
    return handled
def get_searches():
    searches = []

    for location in shuffled(locations):
        for keyword in shuffled(keywords):
            
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
            text = a.get_text(" ", strip=True)
            if evaluate.contains_exclusions(text):
                continue
            href = a["href"]
            if "/jobs/view/" not in href:
                continue 
            
            href = "https://www.linkedin.com" + href if href.startswith("/") else href
            canon = canonical_job_url(href)
            job_urls.add(canon if canon else href)


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

def canonical_job_url(raw: str) -> str | None:
    """
    Return 'https://www.linkedin.com/jobs/view/<id>/' for any flavour of
    LinkedIn job link.  Handles:

      • /jobs/view/4191603147
      • /jobs/view/security-operations-center-...-4191603147
      • /jobs/view/?currentJobId=4191603147
    """
    parsed = urlparse(raw)

    # 1) ID lives somewhere in the path (the common case)
    m = _JOB_ID_RE.search(parsed.path)
    if m:
        job_id = m.group(1)
        return f"https://www.linkedin.com/jobs/view/{job_id}/"

    # 2) ID only appears in the query string (rare but possible)
    qs = parse_qs(parsed.query)
    for key in ("currentJobId", "jobId"):
        if key in qs and qs[key]:
            return f"https://www.linkedin.com/jobs/view/{qs[key][0]}/"

    return None        # caller can fall back to the raw href if desired

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

def extract_job_id(url: str) -> int | None:
    m = _JOB_ID_RE.search(urllib.parse.urlparse(url).path)
    if m:
        return int(m.group(1))
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
    for key in ("currentJobId", "jobId"):
        if key in qs and qs[key]:
            return int(qs[key][0])
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

def get_job_data(job):
    url = job["url"]
    location = job["location"]
    keyword = job["keyword"]
    job_soup = get_soup(url)
    title = ""
    description = ""






    
    job_data = {
        "url": url,
        "location": location,
        "keyword": keyword,
        "title": title,
        "description": description,
    }
    
    return job_data

if __name__ == "__main__":
    searches = get_searches()
    total_links, kept, dropped = 0, 0, 0

    for s in searches:
        soup = get_soup(s["url"])
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/jobs/view/" not in href:
                continue
            total_links += 1
            canon = canonical_job_url("https://www.linkedin.com" + href if href.startswith("/") else href)
            if canon is None:
                dropped += 1
                print("❌  DID NOT MATCH:", href[:120])
            else:
                kept += 1
    print(f"\n{total_links=}  {kept=}  {dropped=}")
