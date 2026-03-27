#!/usr/bin/env python3
"""
Cyber Job Scraper -- Fortune 500 Edition
Scrapes major company career pages for entry-level cybersecurity positions.

ATS platforms covered:
  - Workday        (CrowdStrike, MITRE, Booz Allen, T-Mobile, Comcast, Target, Dell, Walmart)
  - Oracle Cloud   (JPMorgan Chase)
  - iCIMS          (JPMorgan, Bank of America, AT&T, Verizon, Boeing, and more)
  - Taleo/Oracle   (FedEx, UPS, Honeywell, 3M, Caterpillar, and more)
  - SmartRecruiters(Visa, McDonald's, Pfizer, Starbucks, and more)
  - SuccessFactors (ExxonMobil, Chevron, Shell, Siemens, and more)
  - Greenhouse     (Cloudflare, Okta, Huntress, Bugcrowd, and more)
  - Direct APIs    (Amazon, USAJobs/federal government)
  - Custom scrapers(Cisco, IBM)
"""

import time
import requests
from bs4 import BeautifulSoup

from companies import GREENHOUSE_COMPANIES, LEVER_COMPANIES, CUSTOM_COMPANIES
from workday import scrape_all_workday
from direct_api import scrape_all_direct
from icims import scrape_all_icims
from taleo import scrape_all_taleo
from smartrecruiters import scrape_all_smartrecruiters
from successfactors import scrape_all_successfactors
from oracle_cloud import scrape_all_oracle_cloud
from filters import is_entry_level, is_cybersecurity
from output import save_results

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def scrape_greenhouse(company_id, company_name):
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_id}/jobs?content=true"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        jobs = resp.json().get("jobs", [])
        results = []
        for job in jobs:
            title = job.get("title", "")
            if is_cybersecurity(title) and is_entry_level(title, job.get("content", "")):
                results.append({
                    "company": company_name,
                    "title": title,
                    "location": job.get("location", {}).get("name", "N/A"),
                    "url": job.get("absolute_url", ""),
                    "source": "greenhouse",
                })
        return results
    except Exception as e:
        print(f"[!] Greenhouse error for {company_name}: {e}")
        return []


def scrape_lever(company_id, company_name):
    url = f"https://api.lever.co/v0/postings/{company_id}?mode=json"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        jobs = resp.json()
        results = []
        for job in jobs:
            title = job.get("text", "")
            description = job.get("descriptionPlain", "")
            if is_cybersecurity(title) and is_entry_level(title, description):
                results.append({
                    "company": company_name,
                    "title": title,
                    "location": job.get("categories", {}).get("location", "N/A"),
                    "url": job.get("hostedUrl", ""),
                    "source": "lever",
                })
        return results
    except Exception as e:
        print(f"[!] Lever error for {company_name}: {e}")
        return []


def scrape_custom(config):
    company_name = config["name"]
    url = config["url"]
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for item in soup.select(config["job_selector"]):
            title_el = item.select_one(config["title_selector"])
            link_el = item.select_one(config["link_selector"])
            loc_el = item.select_one(config.get("location_selector", "")) if config.get("location_selector") else None

            title = title_el.get_text(strip=True) if title_el else ""
            href = link_el.get("href", "") if link_el else ""
            if href and not href.startswith("http"):
                href = config.get("base_url", "") + href
            location = loc_el.get_text(strip=True) if loc_el else "N/A"

            if title and is_cybersecurity(title) and is_entry_level(title, ""):
                results.append({
                    "company": company_name,
                    "title": title,
                    "location": location,
                    "url": href,
                    "source": "custom",
                })
        return results
    except Exception as e:
        print(f"[!] Custom scrape error for {company_name}: {e}")
        return []


def run():
    all_jobs = []

    print("[*] Workday career pages...")
    all_jobs.extend(scrape_all_workday())

    print("\n[*] Oracle Cloud HCM career pages...")
    all_jobs.extend(scrape_all_oracle_cloud())

    print("\n[*] iCIMS career pages...")
    all_jobs.extend(scrape_all_icims())

    print("\n[*] Taleo/Oracle career pages...")
    all_jobs.extend(scrape_all_taleo())

    print("\n[*] SmartRecruiters career pages...")
    all_jobs.extend(scrape_all_smartrecruiters())

    print("\n[*] SAP SuccessFactors career pages...")
    all_jobs.extend(scrape_all_successfactors())

    print("\n[*] Direct company APIs (Amazon / USAJobs)...")
    all_jobs.extend(scrape_all_direct())

    print("\n[*] Greenhouse career boards...")
    for company_id, company_name in GREENHOUSE_COMPANIES.items():
        print(f"    -> {company_name}")
        all_jobs.extend(scrape_greenhouse(company_id, company_name))
        time.sleep(0.5)

    print("\n[*] Lever career boards...")
    for company_id, company_name in LEVER_COMPANIES.items():
        print(f"    -> {company_name}")
        all_jobs.extend(scrape_lever(company_id, company_name))
        time.sleep(0.5)

    print("\n[*] Custom career pages...")
    for config in CUSTOM_COMPANIES:
        print(f"    -> {config['name']}")
        all_jobs.extend(scrape_custom(config))
        time.sleep(1)

    # Deduplicate by URL
    seen_urls = set()
    unique_jobs = []
    for job in all_jobs:
        if job["url"] not in seen_urls:
            seen_urls.add(job["url"])
            unique_jobs.append(job)

    print(f"\n[+] Found {len(unique_jobs)} matching job(s) across all sources.")
    save_results(unique_jobs)


if __name__ == "__main__":
    run()
