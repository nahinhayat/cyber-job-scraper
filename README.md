# Cyber Job Scraper

Scrapes entry-level cybersecurity job listings across 100+ major companies from the top 500 by market cap. Outputs deduplicated results as JSON and CSV.

## What It Does

Searches career pages for roles matching cybersecurity keywords, then filters out senior/lead/manager positions and physical security jobs, keeping only roles accessible to early-career candidates. A single run typically returns 300–400 unique listings.

**Sources covered:**

| Platform | Companies |
|---|---|
| Workday | Cisco, Intel, Dell, HP, Nvidia, Broadcom, CrowdStrike, MITRE, Booz Allen, Leidos, CACI, T-Mobile, Comcast, Walmart, Target |
| Oracle Cloud HCM | JPMorgan Chase |
| Greenhouse | Cloudflare, GitLab, Okta, Zscaler, Databricks, Huntress, Bugcrowd, Dragos, Airbnb, Nintendo, AppLovin, and more |
| SmartRecruiters | Visa, AbbVie, Bosch, Palantir, LVMH, Uber, ServiceNow, Western Digital, Arista Networks, and more |
| Lever | Palantir, Constellation Energy |
| Playwright (browser) | Apple, Google, Meta, Netflix, Tesla, Microsoft, Goldman Sachs, Morgan Stanley, Bank of America, JPMorgan, Lockheed Martin, Raytheon, Northrop Grumman, Boeing, Palo Alto Networks, Capital One, Citigroup, Wells Fargo, Deloitte, Accenture, PwC, EY, and more |
| Direct API | Amazon, USAJobs (federal government) |

## Setup

**Requirements:** Python 3.9+

```bash
git clone https://github.com/nahinhayat/cyber-job-scraper.git
cd cyber-job-scraper
pip install -r requirements.txt
pip install playwright
playwright install chromium
```

`requirements.txt` covers `requests`, `beautifulsoup4`, and `lxml`. Playwright is needed for the browser-based scrapers (Apple, Google, Meta, most finance/consulting firms).

## Usage

### Run the scraper

```bash
python scraper.py
```

Results are saved to `results/` as both JSON and CSV, timestamped:

```
results/jobs_20260327_155350.json
results/jobs_20260327_155350.csv
```

Each job entry looks like:

```json
{
  "company": "Cloudflare",
  "title": "Security Engineer Intern (Summer 2026)",
  "location": "In-Office",
  "url": "https://boards.greenhouse.io/cloudflare/jobs/7582150",
  "source": "greenhouse"
}
```

### Discover new companies

`discover.py` scrapes the top 500 companies by market cap from [companiesmarketcap.com](https://companiesmarketcap.com), probes each one for Greenhouse, SmartRecruiters, and Lever boards, and saves verified configs to `discovered_companies.json`. The main scraper loads this file automatically.

```bash
# Preview the company list without probing APIs
python discover.py --dry-run

# Run full discovery (takes ~15 minutes, saves progress as it goes)
python discover.py
```

Run `discover.py` periodically to pick up companies that have recently moved to a supported ATS.

### Verify a new Workday company

Before adding a company to `workday.py`, confirm its tenant exposes the public CXS API:

```bash
python verify_workday.py <tenant> <wdN> <site>
# Example:
python verify_workday.py crowdstrike wd5 crowdstrikecareers
```

### USAJobs (federal roles)

Register for a free API key at [developer.usajobs.gov](https://developer.usajobs.gov/apirequest/) and set:

```bash
export USAJOBS_EMAIL=your@email.com
export USAJOBS_API_KEY=your_api_key
```

## How Filtering Works

**`is_cybersecurity(title)`** — returns `True` if the title matches any of:
- Plain keywords: `cyber`, `security`, `infosec`, `pentest`, `vulnerability`, `threat`, `siem`, `firewall`, `devsecops`, `appsec`, etc.
- Word-boundary acronyms: `soc`, `iam`, `grc`
- Context-qualified terms: `compliance` or `risk` when paired with `cyber`, `security`, `information`, or `cloud`

Excluded regardless: billing, marketing, sales, finance, physical security guards, facility security officers, industrial/personnel security, and other non-cyber roles.

**`is_entry_level(title)`** — returns `True` unless the title contains:
- Senior indicators: `senior`, `staff`, `principal`, `lead`, `manager`, `director`, `architect`, `sr.`
- Level suffixes: `II`, `III`, `IV`, `Level 2+`, `Grade 2+`

Titles with no explicit level indicator are included — better to surface a mid-level "Cybersecurity Analyst" than to miss a genuine entry-level role with no label.

## Project Structure

```
scraper.py              # Main entry point — orchestrates all scrapers
workday.py              # Workday CXS API scraper
oracle_cloud.py         # Oracle Cloud HCM scraper (JPMorgan)
playwright_scraper.py   # Headless browser scraper for custom portals
smartrecruiters.py      # SmartRecruiters public API
companies.py            # Static Greenhouse and Lever company lists
direct_api.py           # Amazon and USAJobs direct APIs
filters.py              # Cybersecurity and entry-level keyword filters
output.py               # JSON and CSV export
discover.py             # Auto-discovers ATS platforms for top 500 companies
discovered_companies.json  # Output of discover.py, loaded by scraper.py
verify_workday.py       # CLI tool to test a Workday tenant before adding it
results/                # Timestamped output files
```

## Adding Companies

**Workday** — verify first, then add to `WORKDAY_COMPANIES` in `workday.py`:
```python
"Company Name": ("tenant", "wd1", "SiteName"),
```

**Greenhouse / Lever** — add the board slug to `companies.py`:
```python
GREENHOUSE_COMPANIES = {
    "slugname": "Display Name",
}
```

**Custom portals** — add an entry to `PORTAL_COMPANIES` in `playwright_scraper.py` with the search URL and CSS selectors for title, location, and job link.

**SmartRecruiters** — add to `SMARTRECRUITERS_COMPANIES` in `smartrecruiters.py`:
```python
"Company Name": "slug",
```
