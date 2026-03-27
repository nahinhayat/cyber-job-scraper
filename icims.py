"""
iCIMS ATS scraper.

iCIMS is used by many Fortune 500 companies. Their job boards expose
a public XML/JSON feed that can be queried without authentication.

API endpoint pattern:
  https://careers-{company}.icims.com/jobs/search?schemaState=init&ss=1&searchKeyword=cybersecurity

How to find a company's iCIMS slug:
  1. Visit their careers page — if the URL contains icims.com, note the subdomain.
  2. The slug is the part before .icims.com in careers-{slug}.icims.com
"""

import time
import requests
from bs4 import BeautifulSoup
from filters import is_entry_level, is_cybersecurity

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html",
}

# Format: "company_name": "icims_slug"
# The job board URL is: https://careers-{slug}.icims.com
ICIMS_COMPANIES = {
    "JPMorgan Chase":        "jpmc",
    "Bank of America":       "bankofamerica",
    "Wells Fargo":           "wellsfargo",
    "Citigroup":             "citi",
    "Goldman Sachs":         "goldmansachs",
    "Capital One":           "capitalone",
    "AT&T":                  "att",
    "Verizon":               "verizon",
    "Comcast":               "comcast",
    "UnitedHealth Group":    "unitedhealthgroup",
    "CVS Health":            "cvshealth",
    "Walmart":               "walmart",
    "Target":                "target",
    "General Motors":        "gm",
    "Ford Motor":            "ford",
    "Boeing":                "boeing",
    "Raytheon Technologies": "rtx",
    "General Dynamics":      "gd",
    "L3Harris":              "l3harris",
    "SAIC":                  "saic",
}

SEARCH_TERMS = ["cybersecurity", "security analyst", "information security", "cyber"]


def scrape_icims(company_name, slug):
    """Scrape iCIMS job board for a company."""
    results = []
    seen = set()

    for term in SEARCH_TERMS:
        url = (
            f"https://careers-{slug}.icims.com/jobs/search"
            f"?schemaState=init&ss=1&searchKeyword={requests.utils.quote(term)}"
            f"&in_iframe=1"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            for job_el in soup.select("div.iCIMS_JobsTable div.iCIMS_TableRow, li.iCIMS_ListItemBox"):
                title_el = job_el.select_one("h2 a, .iCIMS_JobTitle a, a.title-link")
                loc_el = job_el.select_one(".iCIMS_JobLocation, .location")

                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                href = title_el.get("href", "")
                if href and not href.startswith("http"):
                    href = f"https://careers-{slug}.icims.com{href}"
                location = loc_el.get_text(strip=True) if loc_el else "N/A"

                if href in seen:
                    continue
                seen.add(href)

                if is_cybersecurity(title) and is_entry_level(title, ""):
                    results.append({
                        "company": company_name,
                        "title": title,
                        "location": location,
                        "url": href,
                        "source": "icims",
                    })

        except Exception as e:
            print(f"[!] iCIMS error for {company_name} ({term}): {e}")

        time.sleep(0.5)

    return results


def scrape_all_icims():
    all_jobs = []
    for company_name, slug in ICIMS_COMPANIES.items():
        print(f"    -> {company_name}")
        all_jobs.extend(scrape_icims(company_name, slug))
        time.sleep(1)
    return all_jobs
