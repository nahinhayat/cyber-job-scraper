"""
Workday career page scraper.

Uses requests for companies whose Workday instances don't enforce CSRF,
and falls back to a headless Playwright browser for companies that do
(these require JavaScript to obtain a valid XSRF-TOKEN session cookie).

How to add a new company:
  1. Visit the company's careers page in your browser.
  2. It will load a Workday URL like:
       https://<tenant>.wd<n>.myworkdayjobs.com/<SITE_NAME>/...
  3. Run: python verify_workday.py <tenant> <wdN> <SITE_NAME>
  4. If it prints OK, add the entry to WORKDAY_COMPANIES below.
"""

import time
from urllib.parse import urlparse

import requests
import requests.exceptions
from filters import is_entry_level, is_cybersecurity

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Format: "Company Name": ("tenant", "wdN", "site_path")
WORKDAY_COMPANIES = {

    # ── Technology ────────────────────────────────────────────────────────────
    # Microsoft uses careers.microsoft.com (not myworkdayjobs.com) → playwright_scraper.py
    "Cisco":              ("cisco",         "wd5", "Cisco_Careers"),
    "Intel":              ("intel",         "wd1", "External"),
    "Salesforce":         ("salesforce",    "wd1", "External"),
    "Dell":               ("dell",          "wd1", "External"),
    "HP Inc":             ("hp",            "wd5", "ExternalCareerSite"),
    "Accenture":          ("accenture",     "wd3", "AccentureCareers"),
    "Nvidia":             ("nvidia",        "wd5", "nvidiaexternalcareersite"),
    "Qualcomm":           ("qualcomm",      "wd5", "External"),
    "Broadcom":           ("broadcom",      "wd1", "External_Career"),

    # ── Cybersecurity (verified) ──────────────────────────────────────────────
    "CrowdStrike":        ("crowdstrike",   "wd5", "crowdstrikecareers"),
    "MITRE":              ("mitre",         "wd5", "MITRE"),

    # ── Finance / Banking ─────────────────────────────────────────────────────
    # JPMorgan, Goldman Sachs, Capital One use custom portals → playwright_scraper.py
    "Bank of America":    ("ghr",           "wd1", "BAC_Professional"),
    "Morgan Stanley":     ("morganstanley", "wd1", "Experienced_Jobs"),
    "American Express":   ("aexp",          "wd5", "amex"),
    "Visa":               ("visa",          "wd1", "VisaJobsGlobal"),
    "Mastercard":         ("mastercard",    "wd1", "mastercardcareers"),
    "PayPal":             ("paypal",        "wd1", "jobsearch"),
    "BlackRock":          ("blackrock",     "wd1", "BlackRock_Careers"),
    "Charles Schwab":     ("schwab",        "wd5", "Schwab"),
    "Fidelity":           ("fmr",           "wd1", "fidelity"),
    "Prudential":         ("prudential",    "wd5", "Careers"),
    "MetLife":            ("metlife",       "wd1", "careers"),
    "Allstate":           ("allstate",      "wd5", "allstate_external"),

    # ── Defense / Government Contractors ─────────────────────────────────────
    "Booz Allen Hamilton": ("bah",          "wd1", "BAH_Jobs"),
    "Lockheed Martin":    ("lmco",          "wd1", "LMCareers"),
    "Raytheon / RTX":     ("rtx",           "wd1", "RTX_Careers"),
    "General Dynamics":   ("gd",            "wd5", "GD_Careers"),
    "Leidos":             ("leidos",        "wd5", "external"),
    "L3Harris":           ("l3harris",      "wd1", "ExternalSite"),
    "SAIC":               ("saic",          "wd1", "SAIC"),
    "Peraton":            ("peraton",       "wd1", "peraton"),
    "Parsons":            ("parsons",       "wd5", "parsons"),
    "CACI":               ("caci",          "wd1", "External"),

    # ── Healthcare ────────────────────────────────────────────────────────────
    "UnitedHealth Group": ("unitedhealthgroup", "wd1", "UHG"),
    "CVS Health":         ("cvs",           "wd1", "CVSHealth"),
    "Cigna":              ("cigna",         "wd1", "Cigna_Careers"),
    "Humana":             ("humana",        "wd5", "Humana_External"),
    "Elevance Health":    ("elevancehealth","wd1", "careers"),
    "HCA Healthcare":     ("hca",           "wd1", "HCA"),
    "McKesson":           ("mckesson",      "wd1", "McKesson"),
    "Cardinal Health":    ("cardinalhealth","wd1", "External"),
    "Johnson & Johnson":  ("jnj",           "wd1", "JNJServices"),
    "Abbott":             ("abbott",        "wd1", "Abbott"),
    "Medtronic":          ("medtronic",     "wd1", "JobBoard"),

    # ── Telecom ───────────────────────────────────────────────────────────────
    "AT&T":               ("att",           "wd1", "ATTCareers"),
    "Verizon":            ("verizon",       "wd1", "jobs"),
    "T-Mobile":           ("tmobile",       "wd1", "External"),
    "Comcast":            ("comcast",       "wd5", "Comcast_Careers"),
    "Charter/Spectrum":   ("charter",       "wd5", "spectrum"),
    "Lumen":              ("lumen",         "wd1", "External"),

    # ── Retail ────────────────────────────────────────────────────────────────
    "Walmart":            ("walmart",       "wd5", "WalmartExternal"),
    "Target":             ("target",        "wd5", "targetcareers"),
    "Home Depot":         ("homedepot",     "wd1", "homedepotcareers"),
    "Lowe's":             ("lowes",         "wd1", "Lowes"),
    "Costco":             ("costco",        "wd5", "Costco_Careers"),
    "Kroger":             ("kroger",        "wd1", "external"),
    "Best Buy":           ("bestbuy",       "wd1", "BBY_External"),

    # ── Consulting ────────────────────────────────────────────────────────────
    "Deloitte":           ("deloitte",      "wd1", "dttl-careers"),
    "PwC":                ("pwc",           "wd3", "Global_Campus_Experienced"),
    "EY":                 ("ey",            "wd5", "ey-careers"),
    "KPMG":               ("kpmg",          "wd1", "KPMG_US"),

    # ── Energy ────────────────────────────────────────────────────────────────
    "ExxonMobil":         ("exxonmobil",    "wd5", "External"),
    "Chevron":            ("chevron",       "wd5", "Chevron"),
    "ConocoPhillips":     ("conocophillips","wd5", "External"),
    "Duke Energy":        ("duke-energy",   "wd1", "Duke_Energy_Careers"),
    "Dominion Energy":    ("dominionenergy","wd5", "External"),
    "NextEra Energy":     ("nextera",       "wd1", "NextEra_Energy_Careers"),

    # ── Manufacturing / Industrial ────────────────────────────────────────────
    "Boeing":             ("boeing",        "wd1", "EXTERNAL_CAREER_SITE"),
    "GE Aerospace":       ("ge",            "wd5", "GE"),
    "Honeywell":          ("honeywell",     "wd5", "Honeywell"),
    "3M":                 ("3m",            "wd1", "3M"),
    "Caterpillar":        ("caterpillar",   "wd5", "CaterpillarCareers"),
    "Deere & Co":         ("deere",         "wd5", "johndeere"),
}

SEARCH_TERMS = ["cybersecurity", "security analyst", "information security"]


def _build_api_url(tenant, wd_num, site):
    return (
        f"https://{tenant}.{wd_num}.myworkdayjobs.com"
        f"/wday/cxs/{tenant}/{site}/jobs"
    )


def _get_session_via_browser(tenant, wd_num, site):
    """
    Launch a headless Chromium browser to load the Workday career page,
    execute JavaScript, and capture the XSRF-TOKEN + Cloudflare cookies.
    Returns (csrf_token, cookie_jar, actual_site_name).
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return "", {}, site

    url = f"https://{tenant}.{wd_num}.myworkdayjobs.com/{site}"
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()
        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
            # Discover actual site from final URL (handles redirects)
            actual_path = urlparse(page.url).path.strip("/").split("/")[0]
            actual_site = actual_path if actual_path and actual_path != "wday" else site
            # Collect cookies
            pw_cookies = context.cookies()
            csrf = next((c["value"] for c in pw_cookies if c["name"] == "XSRF-TOKEN"), "")
            cookie_dict = {c["name"]: c["value"] for c in pw_cookies}
            return csrf, cookie_dict, actual_site
        except Exception:
            return "", {}, site
        finally:
            browser.close()


def scrape_workday(company_name, tenant, wd_num, site):
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    base_url = f"https://{tenant}.{wd_num}.myworkdayjobs.com/{site}"

    # Quick lightweight GET to pick up XSRF-TOKEN if available without JS
    try:
        session.get(base_url, timeout=15)
    except Exception:
        pass

    csrf_token = session.cookies.get("XSRF-TOKEN", "")

    def _make_headers():
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": f"https://{tenant}.{wd_num}.myworkdayjobs.com",
            "Referer": base_url,
        }
        if csrf_token:
            h["X-XSRF-TOKEN"] = csrf_token
        return h

    results = []
    seen = set()
    _browser_attempted = False

    for term in SEARCH_TERMS:
        offset = 0
        api_url = _build_api_url(tenant, wd_num, site)
        while True:
            payload = {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": term}
            try:
                resp = session.post(api_url, headers=_make_headers(), json=payload, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code
                # On 422/401/403/404 try once with a real browser session
                if status in (422, 401, 403, 404) and not _browser_attempted:
                    _browser_attempted = True
                    new_csrf, new_cookies, new_site = _get_session_via_browser(tenant, wd_num, site)
                    if new_cookies:
                        session.cookies.update(new_cookies)
                        csrf_token = new_csrf
                        if new_site != site:
                            site = new_site
                            base_url = f"https://{tenant}.{wd_num}.myworkdayjobs.com/{site}"
                            api_url = _build_api_url(tenant, wd_num, site)
                        continue  # retry this request with the real session
                print(f"[!] Workday error for {company_name} ({term}): {status}")
                break
            except Exception as e:
                print(f"[!] Workday error for {company_name} ({term}): {e}")
                break

            postings = data.get("jobPostings", [])
            if not postings:
                break

            for job in postings:
                title = job.get("title", "")
                job_url = base_url + job.get("externalPath", "")
                if job_url in seen:
                    continue
                seen.add(job_url)
                if is_cybersecurity(title) and is_entry_level(title, ""):
                    results.append({
                        "company": company_name,
                        "title": title,
                        "location": job.get("locationsText", "N/A"),
                        "url": job_url,
                        "source": "workday",
                    })

            total = data.get("total", 0)
            offset += len(postings)
            if offset >= total:
                break
            time.sleep(0.3)

    return results


def scrape_all_workday():
    all_jobs = []
    for company_name, (tenant, wd_num, site) in WORKDAY_COMPANIES.items():
        print(f"    -> {company_name}")
        all_jobs.extend(scrape_workday(company_name, tenant, wd_num, site))
        time.sleep(1)
    return all_jobs
