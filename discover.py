#!/usr/bin/env python3
"""
Auto-discovery tool for ATS platforms across top 500 companies by market cap.

Steps:
  1. Scrape company names from companiesmarketcap.com (pages 1-5, 100 per page)
  2. For each company, guess slug(s) and probe:
       - Greenhouse boards API
       - SmartRecruiters postings API
       - Lever postings API
  3. Save verified configs to discovered_companies.json

Usage:
  python discover.py              # discover all, save to discovered_companies.json
  python discover.py --dry-run    # just print company names, no API probing
"""

import re
import sys
import json
import time
import requests

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}
OUTPUT_FILE = "discovered_companies.json"


# ── Slug generation ────────────────────────────────────────────────────────────

def _slugs(company_name):
    """Generate candidate slugs from a company name."""
    name = company_name.lower()

    # Normalise punctuation/special chars
    clean = re.sub(r"[''`]", "", name)           # apostrophes
    clean = re.sub(r"[&/\\|]", " ", clean)        # separators → space
    clean = re.sub(r"[^a-z0-9 .-]", "", clean)   # strip anything else
    clean = clean.strip()

    words = clean.split()
    candidates = []

    # "amazon.com" → "amazon"
    stripped = re.sub(r"\.(com|inc|corp|ltd|llc|co|net|org)$", "", clean).strip()
    if stripped and stripped != clean:
        sw = stripped.split()
        candidates.append("".join(sw))
        candidates.append("-".join(sw))
        candidates.append(sw[0])

    # Remove common suffixes for shorter slugs
    noise = {
        "inc", "corp", "corporation", "ltd", "llc", "co", "company",
        "group", "holdings", "holding", "technologies", "technology",
        "solutions", "services", "systems", "international", "global",
        "enterprises", "enterprise",
    }
    filtered = [w for w in words if w not in noise]
    if not filtered:
        filtered = words[:1]

    # Full joined variants
    candidates.append("".join(filtered))
    candidates.append("-".join(filtered))
    candidates.append("".join(words))
    candidates.append("-".join(words))

    # First word only (most common slug pattern)
    candidates.append(words[0])
    if filtered:
        candidates.append(filtered[0])

    # Two-word prefix
    if len(filtered) >= 2:
        candidates.append("".join(filtered[:2]))
        candidates.append("-".join(filtered[:2]))
    if len(words) >= 2:
        candidates.append("".join(words[:2]))

    # Deduplicate while preserving order
    seen = set()
    result = []
    for s in candidates:
        s = s.strip("-").strip()
        if s and s not in seen:
            seen.add(s)
            result.append(s)
    return result


# ── Platform probers ───────────────────────────────────────────────────────────

def _probe_greenhouse(slug, timeout=8):
    # Require slug >= 5 chars to avoid matching generic short boards unrelated to the company.
    # Also require at least 1 active job so we know it's a real, active board.
    if len(slug) < 5:
        return False
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            # Require >= 10 jobs to filter out small unrelated boards that happen
            # to share a short slug with the target company.
            if len(data.get("jobs", [])) >= 10:
                return True
    except Exception:
        pass
    return False


def _probe_smartrecruiters(slug, timeout=8):
    # SmartRecruiters returns 200 for ANY slug (even non-existent companies).
    # The only reliable signal is totalFound > 0 on a broad search.
    url = f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=1"
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            if data.get("totalFound", 0) > 0:
                return True
    except Exception:
        pass
    return False


def _probe_lever(slug, timeout=8):
    # Lever returns an empty list [] for nonexistent companies on some slugs.
    # Require at least 1 posting to confirm it's a real board.
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json&limit=1"
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and len(data) > 0:
                return True
    except Exception:
        pass
    return False


def _discover_ats(company_name):
    """
    Try all slug variants against each supported ATS.
    Returns a dict with keys: greenhouse, smartrecruiters, lever
    Each value is the working slug or None.
    """
    result = {"greenhouse": None, "smartrecruiters": None, "lever": None}
    slugs = _slugs(company_name)

    for slug in slugs:
        if not result["greenhouse"] and _probe_greenhouse(slug):
            result["greenhouse"] = slug
        if not result["smartrecruiters"] and _probe_smartrecruiters(slug):
            result["smartrecruiters"] = slug
        if not result["lever"] and _probe_lever(slug):
            result["lever"] = slug

        # Stop early if we found something on all three
        if all(result.values()):
            break

        time.sleep(0.15)

    return result


# ── Company list scraper ───────────────────────────────────────────────────────

def fetch_top_500():
    """Scrape the top 500 companies from companiesmarketcap.com (pages 1-5)."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("[!] beautifulsoup4 not installed. Run: pip install beautifulsoup4")
        sys.exit(1)

    companies = []
    page_headers = {"User-Agent": USER_AGENT}

    for page in range(1, 6):
        url = f"https://companiesmarketcap.com/?page={page}"
        print(f"  Fetching page {page}/5 from companiesmarketcap.com...")
        try:
            r = requests.get(url, headers=page_headers, timeout=20)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            names = [el.get_text(strip=True) for el in soup.select("div.company-name")]
            companies.extend(names)
            print(f"    Found {len(names)} companies on page {page}")
        except Exception as e:
            print(f"[!] Failed to fetch page {page}: {e}")
        time.sleep(1)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for name in companies:
        if name and name not in seen:
            seen.add(name)
            unique.append(name)

    return unique


# ── Skip list (already handled by dedicated scrapers) ─────────────────────────

# Companies already covered by workday.py, oracle_cloud.py, or playwright_scraper.py
ALREADY_COVERED = {
    "NVIDIA", "Cisco", "Intel", "Dell Technologies", "Dell", "HP Inc", "Broadcom",
    "CrowdStrike", "MITRE", "Booz Allen Hamilton", "Leidos", "CACI", "T-Mobile",
    "Comcast", "Walmart", "Target", "JPMorgan Chase", "Microsoft", "Lockheed Martin",
    "Raytheon", "RTX", "General Dynamics", "L3Harris", "SAIC", "Salesforce",
    "Goldman Sachs", "Morgan Stanley", "Boeing", "Verizon", "AT&T",
    "UnitedHealth Group", "CVS Health", "Johnson & Johnson", "Bank of America",
}


# ── Main ───────────────────────────────────────────────────────────────────────

def run(dry_run=False):
    print("[*] Fetching top 500 companies from companiesmarketcap.com...")
    companies = fetch_top_500()
    print(f"[+] Scraped {len(companies)} companies total.\n")

    if dry_run:
        for i, name in enumerate(companies, 1):
            print(f"  {i:3d}. {name}")
        return

    # Load existing results to allow resuming
    try:
        with open(OUTPUT_FILE) as f:
            discovered = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        discovered = {}

    already_checked = set(discovered.keys())

    to_check = [
        c for c in companies
        if c not in already_checked and c not in ALREADY_COVERED
    ]

    print(f"[*] {len(to_check)} companies to probe (skipping {len(already_checked)} already checked, "
          f"{len([c for c in companies if c in ALREADY_COVERED])} already covered).\n")

    found_count = 0
    for i, company in enumerate(to_check, 1):
        print(f"  [{i}/{len(to_check)}] {company}...")
        ats = _discover_ats(company)

        discovered[company] = ats

        platforms = [p for p, slug in ats.items() if slug]
        if platforms:
            found_count += 1
            for platform, slug in ats.items():
                if slug:
                    print(f"    ✓ {platform}: {slug}")
        else:
            print(f"    - no supported ATS found")

        # Save progress every 10 companies
        if i % 10 == 0:
            with open(OUTPUT_FILE, "w") as f:
                json.dump(discovered, f, indent=2)
            print(f"    [saved progress: {i}/{len(to_check)}]")

        time.sleep(0.5)

    # Final save
    with open(OUTPUT_FILE, "w") as f:
        json.dump(discovered, f, indent=2)

    print(f"\n[+] Done. Found supported ATS for {found_count}/{len(to_check)} companies.")
    print(f"[+] Results saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    run(dry_run=dry)
