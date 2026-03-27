"""
Workday career page scraper.

How to add a new company:
  1. Visit the company's careers page in your browser.
  2. It will load a Workday URL like:
       https://<tenant>.wd<n>.myworkdayjobs.com/<SITE_NAME>/...
  3. Run: python verify_workday.py <tenant> <wdN> <SITE_NAME>
  4. If it prints OK, add the entry to WORKDAY_COMPANIES below.
"""

import time
import requests
import requests.exceptions
from filters import is_entry_level, is_cybersecurity

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Format: "Company Name": ("tenant", "wdN", "site_path")
WORKDAY_COMPANIES = {

    # ── Technology ────────────────────────────────────────────────────────────
    "Microsoft":          ("microsoft",     "wd1", "microsoftcareers"),
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
    "JPMorgan Chase":     ("jpmc",          "wd5", "JPMCCareers"),
    "Bank of America":    ("ghr",           "wd1", "BAC_Professional"),
    "Goldman Sachs":      ("goldmansachs",  "wd1", "gs"),
    "Morgan Stanley":     ("morganstanley", "wd1", "Experienced_Jobs"),
    "Capital One":        ("capitalone",    "wd1", "Capital_One"),
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


def scrape_workday(company_name, tenant, wd_num, site):
    api_url = _build_api_url(tenant, wd_num, site)
    base_url = f"https://{tenant}.{wd_num}.myworkdayjobs.com/{site}"

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    try:
        session.get(base_url, timeout=15)
    except Exception:
        pass

    csrf_token = session.cookies.get("XSRF-TOKEN", "")
    post_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": f"https://{tenant}.{wd_num}.myworkdayjobs.com",
        "Referer": base_url,
    }
    if csrf_token:
        post_headers["X-XSRF-TOKEN"] = csrf_token

    results = []
    seen = set()

    for term in SEARCH_TERMS:
        offset = 0
        while True:
            payload = {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": term}
            try:
                resp = session.post(api_url, headers=post_headers, json=payload, timeout=15)
                resp.raise_for_status()
                data = resp.json()
            except requests.exceptions.HTTPError as e:
                print(f"[!] Workday error for {company_name} ({term}): {e.response.status_code}")
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
