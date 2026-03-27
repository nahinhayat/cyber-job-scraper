"""
Playwright-based scraper for companies whose career sites are JavaScript-rendered
and don't expose a simple public API.

Strategy: navigate to the company's cybersecurity search URL, intercept the
underlying API/XHR calls the page makes, and extract job data from the responses.
Falls back to HTML parsing if no API call is captured.
"""

import json
import time
from filters import is_entry_level, is_cybersecurity

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Each entry: (company_name, search_url, hint)
# hint: a substring that the job-listing API response URL must contain
PLAYWRIGHT_COMPANIES = [
    (
        "JPMorgan Chase",
        "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?keyword=cybersecurity",
        "requisitions",
    ),
    (
        "Microsoft",
        "https://careers.microsoft.com/v2/global/en/search.html?q=cybersecurity&lc=United+States&l=en_us",
        "search",
    ),
    (
        "Goldman Sachs",
        "https://higher.gs.com/roles?query=cybersecurity",
        "roles",
    ),
    (
        "Capital One",
        "https://www.capitalonecareers.com/search-jobs?keywords=cybersecurity",
        "jobs",
    ),
    (
        "IBM",
        "https://www.ibm.com/us-en/employment/newhire/#jobs?field_keyword_08[]=Cybersecurity&field_keyword_05[]=Entry+Level",
        "employment",
    ),
]


def _extract_jobs_from_response(company_name, url, body_text):
    """
    Try to parse jobs out of a captured API response body.
    Handles several common JSON schemas used by career platforms.
    """
    try:
        data = json.loads(body_text)
    except Exception:
        return []

    jobs = []

    # Oracle Cloud HCM schema
    if "items" in data:
        for item in data.get("items", []):
            for job in item.get("requisitionList", [item]):
                title = job.get("Title", job.get("requisitionTitle", job.get("title", "")))
                req_id = str(job.get("Id", job.get("requisitionId", job.get("id", ""))))
                loc = job.get("PrimaryLocation", job.get("primaryLocation", job.get("locationName", "N/A")))
                job_url = job.get("ExternalURL", job.get("externalURL", ""))
                if title and is_cybersecurity(title) and is_entry_level(title, ""):
                    jobs.append({"company": company_name, "title": title,
                                 "location": loc, "url": job_url, "source": "playwright"})

    # Microsoft / generic {value: [...]} schema
    elif "value" in data:
        for job in data.get("value", []):
            title = job.get("title", job.get("jobTitle", ""))
            loc = job.get("location", job.get("primaryLocation", "N/A"))
            job_url = job.get("applyUrl", job.get("url", job.get("jobDetailUrl", "")))
            if title and is_cybersecurity(title) and is_entry_level(title, ""):
                jobs.append({"company": company_name, "title": title,
                             "location": loc, "url": job_url, "source": "playwright"})

    # {jobs: [...]} or {results: [...]} or {postings: [...]}
    else:
        for key in ("jobs", "results", "postings", "data", "jobPostings"):
            if key in data:
                for job in data[key]:
                    title = job.get("title", job.get("jobTitle", job.get("name", "")))
                    loc = job.get("location", job.get("locationName", job.get("locationsText", "N/A")))
                    job_url = job.get("url", job.get("applyUrl", job.get("absoluteUrl", job.get("hostedUrl", ""))))
                    if title and is_cybersecurity(title) and is_entry_level(title, ""):
                        jobs.append({"company": company_name, "title": title,
                                     "location": loc, "url": job_url, "source": "playwright"})
                break

    return jobs


def _scrape_with_intercept(company_name, search_url, hint):
    """Navigate to the search URL, capture API responses, extract jobs."""
    from playwright.sync_api import sync_playwright

    captured = []

    def handle_response(response):
        url = response.url
        if hint in url.lower() and response.status == 200:
            try:
                body = response.body()
                jobs = _extract_jobs_from_response(company_name, url, body)
                if jobs:
                    captured.extend(jobs)
            except Exception:
                pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()
        page.on("response", handle_response)
        try:
            page.goto(search_url, wait_until="networkidle", timeout=30000)
            # Wait a bit more for lazy-loaded content
            page.wait_for_timeout(3000)
        except Exception:
            pass
        browser.close()

    return captured


def scrape_all_playwright():
    all_jobs = []
    for company_name, search_url, hint in PLAYWRIGHT_COMPANIES:
        print(f"    -> {company_name}")
        try:
            jobs = _scrape_with_intercept(company_name, search_url, hint)
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"[!] Playwright error for {company_name}: {e}")
        time.sleep(1)
    return all_jobs
