"""
Direct career API scrapers for companies that expose public job search endpoints.

Covers: Microsoft, Google, Amazon, and USAJobs (federal government).
No authentication or browser required — all are public JSON APIs.
"""

import time
import requests
from filters import is_entry_level, is_cybersecurity

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; CyberJobScraper/1.0)",
    "Accept": "application/json",
}


def scrape_microsoft() -> list[dict]:
    """
    Microsoft careers search API.
    Searches for cybersecurity/security roles and filters entry-level.
    """
    results = []
    seen = set()
    search_terms = ["cybersecurity", "security analyst", "security engineer"]

    for term in search_terms:
        page = 1
        while True:
            url = (
                "https://gcsservices.careers.microsoft.com/search/api/v1/search"
                f"?q={requests.utils.quote(term)}&l=en_us&pg={page}&pgSz=20&o=Recent&flt=true"
            )
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[!] Microsoft API error ({term}): {e}")
                break

            jobs = data.get("operationResult", {}).get("result", {}).get("jobs", [])
            if not jobs:
                break

            for job in jobs:
                job_id = job.get("jobId", "")
                if job_id in seen:
                    continue
                seen.add(job_id)

                title = job.get("title", "")
                if is_cybersecurity(title) and is_entry_level(title, job.get("jobSummary", "")):
                    location = ", ".join(
                        loc.get("city", "") for loc in job.get("primaryLocations", [])
                    ) or "N/A"
                    results.append({
                        "company": "Microsoft",
                        "title": title,
                        "location": location,
                        "url": f"https://careers.microsoft.com/us/en/job/{job_id}",
                        "source": "microsoft",
                    })

            total_pages = data.get("operationResult", {}).get("result", {}).get("totalPages", 1)
            if page >= total_pages:
                break
            page += 1
            time.sleep(0.5)

    return results


def scrape_google() -> list[dict]:
    """
    Google careers search API.
    """
    results = []
    seen = set()
    search_terms = ["cybersecurity", "security engineer", "information security"]

    for term in search_terms:
        page = 1
        while True:
            url = (
                "https://careers.google.com/api/v3/search/"
                f"?q={requests.utils.quote(term)}&employment_type=FULL_TIME"
                f"&jlo=en_US&page_size=20&page={page}"
            )
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"[!] Google API error ({term}): {e}")
                break

            jobs = data.get("jobs", [])
            if not jobs:
                break

            for job in jobs:
                job_id = job.get("id", "")
                if job_id in seen:
                    continue
                seen.add(job_id)

                title = job.get("title", "")
                description = job.get("description", "")
                if is_cybersecurity(title) and is_entry_level(title, description):
                    locations = job.get("locations", [])
                    location = locations[0].get("display", "N/A") if locations else "N/A"
                    results.append({
                        "company": "Google",
                        "title": title,
                        "location": location,
                        "url": f"https://careers.google.com/jobs/results/{job_id}",
                        "source": "google",
                    })

            next_page = data.get("next_page_token")
            if not next_page:
                break
            page += 1
            time.sleep(0.5)

    return results


def scrape_amazon() -> list[dict]:
    """
    Amazon jobs search API.
    """
    results = []
    seen = set()

    url = (
        "https://www.amazon.jobs/en/search.json"
        "?base_query=cybersecurity+security&country=US"
        "&category=security&result_limit=100&offset=0"
    )
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[!] Amazon API error: {e}")
        return []

    for job in data.get("jobs", []):
        job_id = job.get("id", "")
        if job_id in seen:
            continue
        seen.add(job_id)

        title = job.get("title", "")
        description = job.get("description", "")
        if is_cybersecurity(title) and is_entry_level(title, description):
            results.append({
                "company": "Amazon",
                "title": title,
                "location": job.get("normalized_location", "N/A"),
                "url": "https://www.amazon.jobs" + job.get("job_path", ""),
                "source": "amazon",
            })

    return results


def scrape_usajobs() -> list[dict]:
    """
    USAJobs public API — federal government cybersecurity openings.
    GS-05 through GS-09 are entry/junior level grades.

    Requires a free API key: register at https://developer.usajobs.gov/apirequest/
    Set your email and API key in environment variables:
      export USAJOBS_EMAIL=your@email.com
      export USAJOBS_API_KEY=your_api_key
    """
    import os

    user_agent = os.getenv("USAJOBS_EMAIL", "")
    api_key = os.getenv("USAJOBS_API_KEY", "")

    if not user_agent or not api_key:
        print("[!] USAJobs: set USAJOBS_EMAIL and USAJOBS_API_KEY env vars to enable.")
        return []

    headers = {
        "Host": "data.usajobs.gov",
        "User-Agent": user_agent,
        "Authorization-Key": api_key,
    }

    url = (
        "https://data.usajobs.gov/api/search"
        "?Keyword=cybersecurity&PayGradeHigh=09&ResultsPerPage=50"
    )
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[!] USAJobs API error: {e}")
        return []

    results = []
    for item in data.get("SearchResult", {}).get("SearchResultItems", []):
        matched = item.get("MatchedObjectDescriptor", {})
        title = matched.get("PositionTitle", "")
        if is_cybersecurity(title) and is_entry_level(title, matched.get("QualificationSummary", "")):
            results.append({
                "company": matched.get("OrganizationName", "US Government"),
                "title": title,
                "location": matched.get("PositionLocationDisplay", "N/A"),
                "url": matched.get("PositionURI", ""),
                "source": "usajobs",
            })

    return results


def scrape_all_direct() -> list[dict]:
    all_jobs = []

    print("    -> Microsoft")
    all_jobs.extend(scrape_microsoft())
    time.sleep(1)

    print("    -> Google")
    all_jobs.extend(scrape_google())
    time.sleep(1)

    print("    -> Amazon")
    all_jobs.extend(scrape_amazon())
    time.sleep(1)

    print("    -> USAJobs (Federal)")
    all_jobs.extend(scrape_usajobs())

    return all_jobs
