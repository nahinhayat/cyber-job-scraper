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
        "https://morganstanley.eightfold.ai/careers?query=cybersecurity",
        "[class*='job-title'], [class*='JobTitle'], h4, h3",
        "[class*='location'], [class*='Location']",
        "a[href*='/careers/jobs/']",
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

    # ── Big Tech (own portals) ─────────────────────────────────────────────────
    (
        "Apple",
        "https://jobs.apple.com/en-us/search?search=cybersecurity&sort=relevance",
        "#search-results .table-col-1 a, .table--advanced-search__title a, td.table-col-1 a",
        ".table-col-2, .table--advanced-search__location, td.table-col-2",
        "#search-results .table-col-1 a, td.table-col-1 a",
    ),
    (
        "Google",
        "https://careers.google.com/jobs/results/?q=cybersecurity&location=United+States",
        "li.lLd3Je h3, .QJPWVe, [data-is-expandable] h3, li[class*='job'] h3",
        ".r0wTof, [class*='location'], [class*='Location']",
        "a[href*='/jobs/results/']",
    ),
    (
        "Meta",
        "https://www.metacareers.com/jobs?q=cybersecurity&teams[0]=Security%2C+Safety+%26+Privacy",
        "[data-testid*='title'], ._8muv h3, h2[class*='title'], h3[class*='title']",
        "[data-testid*='location'], ._8x74, [class*='location']",
        "a[href*='/jobs/']",
    ),
    (
        "Netflix",
        "https://jobs.netflix.com/search?q=cybersecurity",
        "[data-testid='job-title'], h3[class*='Title'], .JobCard__title, h3",
        "[data-testid='job-location'], [class*='location'], .location",
        "a[href*='/jobs/']",
    ),
    (
        "Tesla",
        "https://www.tesla.com/careers/search?query=cybersecurity&country=US",
        "[data-testid='result-title'], .result-title, h3[class*='title'], h3",
        "[data-testid='result-location'], .result-location, [class*='location']",
        "a[href*='/careers/search/job']",
    ),
    (
        "Oracle",
        "https://careers.oracle.com/jobs/#en/sites/jobsearch/requisitions?keyword=cybersecurity",
        "li.jobs-list-item .title a, a.job-title, [class*='JobTitle'], h3",
        ".location, [class*='location']",
        "li.jobs-list-item .title a, a[href*='/requisitions/preview/']",
    ),
    (
        "PayPal",
        "https://careers.pypl.com/jobs/#en/sites/paypal/requisitions?keyword=cybersecurity",
        "li.jobs-list-item .title a, a.job-title, [class*='JobTitle'], h3",
        ".location, [class*='location']",
        "a[href*='/requisitions/preview/']",
    ),
    (
        "Palo Alto Networks",
        "https://jobs.paloaltonetworks.com/en-US/search?keywords=cybersecurity",
        "h2.job-title, .job-info h2, [class*='JobTitle'], h3",
        ".job-location, [class*='location']",
        "a[href*='/job/']",
    ),
    (
        "Fortinet",
        "https://careers.fortinet.com/jobs/search?keywords=cybersecurity",
        ".job-title a, h3.title, [class*='title']",
        ".location, [class*='location']",
        ".job-title a, a[href*='/jobs/']",
    ),
    (
        "Qualcomm",
        "https://careers.qualcomm.com/careers/search?q=cybersecurity&location=United+States",
        "h3[class*='heading'], .job-listing-title, a.job-title-link, h3",
        ".location, [class*='location']",
        "a.job-title-link, a[href*='/careers/']",
    ),
    (
        "AMD",
        "https://careers.amd.com/careers-home/jobs?keywords=cybersecurity",
        ".job-list-item-title, h3[class*='title'], [class*='JobTitle'], h3",
        ".job-location, [class*='location']",
        "a[href*='/careers-home/jobs/']",
    ),
    (
        "Texas Instruments",
        "https://careers.ti.com/jobs?q=cybersecurity",
        ".job-title a, h3.title, a[class*='title'], h3",
        ".location, [class*='location']",
        ".job-title a, a[href*='/job/']",
    ),
    (
        "Intuit",
        "https://careers.intuit.com/job-search-results/?keyword=cybersecurity",
        ".job-title a, h2.title, [class*='JobTitle']",
        ".job-location, .location",
        ".job-title a",
    ),
    (
        "Snowflake",
        "https://careers.snowflake.com/us/en/search-results?keywords=cybersecurity",
        ".job-title, h3[class*='Title'], [class*='JobTitle'], h3",
        ".location, [class*='location']",
        "a[href*='/job/']",
    ),
    (
        "Datadog",
        "https://careers.datadoghq.com/all-jobs?search=cybersecurity",
        "h5.career-listing__title, h3, [class*='title']",
        ".career-listing__location, .location",
        "a[href*='/jobs/']",
    ),

    # ── Finance (own portals) ──────────────────────────────────────────────────
    (
        "Mastercard",
        "https://careers.mastercard.com/us/en/search-results?keywords=cybersecurity",
        ".job-title, h3[class*='Title'], [class*='JobTitle']",
        ".location, [class*='location']",
        "a[href*='/job/']",
    ),
    (
        "Capital One",
        "https://www.capitalonecareers.com/search-jobs?keywords=cybersecurity",
        ".iCIMS_JobTitle a, .job-title a, h2.title",
        ".iCIMS_Location, .job-location, .location",
        ".iCIMS_JobTitle a, .job-title a",
    ),
    (
        "American Express",
        "https://aexp.avature.net/careers/SearchJobs/cybersecurity",
        "h3.results-list__title a, .job-title a, h3",
        ".job-location, .location",
        "h3.results-list__title a, a[href*='/careers/']",
    ),
    (
        "Citigroup",
        "https://jobs.citi.com/search-jobs?keyword=cybersecurity",
        ".job-title a, h2.title, [class*='JobTitle']",
        ".job-location, .location",
        ".job-title a",
    ),
    (
        "Wells Fargo",
        "https://www.wellsfargojobs.com/en/jobs/?keyword=cybersecurity",
        ".job-title a, h2.title, [class*='JobTitle']",
        ".job-location, .location",
        ".job-title a",
    ),

    # ── Defense / Consulting ───────────────────────────────────────────────────
    (
        "Northrop Grumman",
        "https://www.northropgrumman.com/jobs/?search=cybersecurity",
        ".job-title a, h3[class*='title'], [class*='JobTitle'], h3",
        ".location, [class*='location']",
        ".job-title a, a[href*='/jobs/']",
    ),
    (
        "Accenture",
        "https://www.accenture.com/us-en/careers/jobsearch?jk=cybersecurity&c=us",
        ".cmp-teaser__title a, h5[class*='title'], h3, [class*='Title']",
        ".cmp-teaser__location, .location, [class*='location']",
        ".cmp-teaser__title a, a[href*='/careers/job']",
    ),
    (
        "Deloitte",
        "https://apply.deloitte.com/careers/SearchJobs/cybersecurity",
        ".ListJobsTable .colTitle a, .job-title a, td.colTitle a",
        ".colLocation, .location",
        ".ListJobsTable .colTitle a, td.colTitle a",
    ),
    (
        "PwC",
        "https://jobs.us.pwc.com/search-jobs?keywords=cybersecurity",
        ".iCIMS_JobTitle a, .job-title a, h2.title",
        ".iCIMS_Location, .job-location",
        ".iCIMS_JobTitle a, .job-title a",
    ),
    (
        "EY",
        "https://careers.ey.com/ey/search/?q=%22cybersecurity%22&countryname=United+States+of+America",
        ".job-title a, h3[class*='title'], h3, [class*='JobTitle']",
        ".location, [class*='location']",
        ".job-title a, a[href*='/job/']",
    ),
    (
        "Kforce",
        "https://www.kforce.com/job-seekers/technology-jobs/?q=cybersecurity",
        ".job-title a, h3, [class*='title']",
        ".location, [class*='location']",
        ".job-title a, a[href*='/job/']",
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
            page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(5000)

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
                    texts = []
                    for e in els:
                        try:
                            texts.append(e.inner_text().strip())
                        except Exception:
                            texts.append("")
                    locations = texts
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
