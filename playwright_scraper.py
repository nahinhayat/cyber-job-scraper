"""
Playwright-based scraper for companies that use custom career portals
(not public-facing Workday APIs).

Navigates to each company's cybersecurity job search URL, waits for
the page to render, then extracts job listings from the DOM.
"""

import time
from filters import is_entry_level, is_cybersecurity

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Each entry: (company_name, search_url, title_selector, location_selector, link_selector)
# link_selector: CSS selector for <a> tag; if relative, base_url is prepended
PORTAL_COMPANIES = [
    (
        "JPMorgan Chase",
        "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs?keyword=cybersecurity",
        "h3.job-item-title, span.job-requisition-title, [data-bind*='title']",
        ".job-location, [data-bind*='location']",
        "a.job-list-item-link, a[href*='requisitions/preview']",
    ),
    (
        "Microsoft",
        "https://jobs.careers.microsoft.com/global/en/search?q=cybersecurity&l=en_us&pg=1&pgSz=20&o=Recent&flt=true",
        "h2.job-title, .ms-List-cell h2, [class*='JobTitle']",
        "[class*='location'], [class*='Location']",
        "a[href*='jobs.careers.microsoft.com']",
    ),
    (
        "Lockheed Martin",
        "https://www.lockheedmartinjobs.com/search-jobs?keyword=cybersecurity",
        ".job-title a, h2.title",
        ".job-location, .location",
        ".job-title a",
    ),
    (
        "Raytheon / RTX",
        "https://jobs.rtx.com/search-jobs?keyword=cybersecurity",
        ".job-title a, h2.title",
        ".job-location, .location",
        ".job-title a",
    ),
    (
        "General Dynamics",
        "https://gdmissionsystems.com/careers/find-a-job?q=cybersecurity",
        ".job-title, h3.title",
        ".location",
        "a[href*='careers']",
    ),
    (
        "L3Harris",
        "https://careers.l3harris.com/search-jobs?keyword=cybersecurity",
        ".job-title a, h2.title",
        ".job-location",
        ".job-title a",
    ),
    (
        "SAIC",
        "https://jobs.saic.com/jobs?keywords=cybersecurity",
        ".job-title, h3.title, a.job-name",
        ".location",
        "a.job-name, a[href*='/jobs/']",
    ),
    (
        "Salesforce",
        "https://careers.salesforce.com/en/jobs/?search=cybersecurity&team=Information+Security",
        ".career-card__title, h3.job-title, [class*='JobTitle']",
        ".career-card__location, .location",
        "a[href*='/en/jobs/']",
    ),
    (
        "Goldman Sachs",
        "https://higher.gs.com/roles?query=cybersecurity",
        "h3, [class*='title'], [class*='Title']",
        "[class*='location'], [class*='Location']",
        "a[href*='/roles/']",
    ),
    (
        "Morgan Stanley",
        "https://www.morganstanley.com/people-opportunities/students-graduates/programs?q=cybersecurity",
        ".job-title, h3",
        ".location",
        "a[href*='morganstanley.com']",
    ),
    (
        "Boeing",
        "https://jobs.boeing.com/search-jobs?keyword=cybersecurity",
        ".job-title a, h2.title",
        ".job-location",
        ".job-title a",
    ),
    (
        "Verizon",
        "https://mycareer.verizon.com/jobs/search/?keyword=cybersecurity",
        ".job-title, h3.title, [class*='JobTitle']",
        ".location, [class*='location']",
        "a[href*='/jobs/']",
    ),
    (
        "AT&T",
        "https://www.att.jobs/search-jobs?keyword=cybersecurity",
        ".job-title a, h2.title",
        ".job-location",
        ".job-title a",
    ),
    (
        "UnitedHealth Group",
        "https://careers.unitedhealthgroup.com/job-search-results/?keyword=cybersecurity",
        ".job-title a, h2.title, [class*='JobTitle']",
        ".job-location, [class*='location']",
        ".job-title a, a[href*='/job/']",
    ),
    (
        "CVS Health",
        "https://jobs.cvshealth.com/us/en/search-results?keywords=cybersecurity",
        ".job-title, h3.title",
        ".location",
        "a[href*='/job/']",
    ),
    (
        "Johnson & Johnson",
        "https://jobs.jnj.com/en/jobs?q=cybersecurity",
        ".job-title, h3, [class*='Title']",
        "[class*='location']",
        "a[href*='/jobs/']",
    ),
    (
        "Bank of America",
        "https://careers.bankofamerica.com/en-us/job-search-results?keywords=cybersecurity",
        ".job-title, h3.title, [class*='JobTitle']",
        ".job-location, [class*='location']",
        "a[href*='/job/']",
    ),
]


def _scrape_portal(company_name, search_url, title_sel, loc_sel, link_sel):
    """Navigate to the search page and extract jobs from rendered DOM."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(f"[!] Playwright not installed — skipping {company_name}")
        return []

    results = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()
        try:
            page.goto(search_url, wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            # Try each title selector
            titles = []
            for sel in title_sel.split(", "):
                els = page.locator(sel).all()
                if els:
                    titles = [e.inner_text().strip() for e in els if e.inner_text().strip()]
                    break

            # Try each location selector
            locations = []
            for sel in loc_sel.split(", "):
                els = page.locator(sel).all()
                if els:
                    locations = [e.inner_text().strip() for e in els]
                    break

            # Try each link selector
            links = []
            for sel in link_sel.split(", "):
                els = page.locator(sel).all()
                if els:
                    links = [e.get_attribute("href") or "" for e in els]
                    break

            # Zip them up (pad shorter lists with defaults)
            for i, title in enumerate(titles):
                if not title:
                    continue
                location = locations[i] if i < len(locations) else "N/A"
                href = links[i] if i < len(links) else ""
                if href and not href.startswith("http"):
                    from urllib.parse import urlparse
                    base = f"{urlparse(search_url).scheme}://{urlparse(search_url).netloc}"
                    href = base + href

                if href in seen:
                    continue
                seen.add(href)

                if is_cybersecurity(title) and is_entry_level(title, ""):
                    results.append({
                        "company": company_name,
                        "title": title,
                        "location": location,
                        "url": href,
                        "source": "playwright",
                    })

        except Exception as e:
            print(f"[!] Playwright error for {company_name}: {e}")
        finally:
            browser.close()

    return results


def scrape_all_playwright():
    all_jobs = []
    for company_name, search_url, title_sel, loc_sel, link_sel in PORTAL_COMPANIES:
        print(f"    -> {company_name}")
        try:
            jobs = _scrape_portal(company_name, search_url, title_sel, loc_sel, link_sel)
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"[!] Playwright error for {company_name}: {e}")
        time.sleep(1)
    return all_jobs
