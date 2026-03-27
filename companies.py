"""
Company configurations.

GREENHOUSE_COMPANIES: {greenhouse_board_id: display_name}
LEVER_COMPANIES:      {lever_company_slug: display_name}
CUSTOM_COMPANIES:     list of dicts with CSS selector configs

--- How to find a company's ATS board ID ---
Greenhouse: Visit their careers page, look for a URL like
    boards.greenhouse.io/<board_id>  or
    job-boards.greenhouse.io/<board_id>
    The <board_id> is the slug to use here.

Lever: Visit their careers page, look for a URL like
    jobs.lever.co/<company_slug>
    The <company_slug> is the slug to use here.

NOTE: CrowdStrike, Palo Alto Networks, Raytheon, and many large
defense/enterprise security firms use Workday, not Greenhouse/Lever.
Those are handled in workday.py.
"""

# Companies using Greenhouse ATS (verified board IDs)
GREENHOUSE_COMPANIES = {
    "gitlab": "GitLab",
    "cloudflare": "Cloudflare",
    "okta": "Okta",
    "huntress": "Huntress",
    "bugcrowd": "Bugcrowd",
    "palantir": "Palantir",
    "zscaler": "Zscaler",
    "sentinelone": "SentinelOne",
    "rapid7": "Rapid7",
    "tenable": "Tenable",
    "databricks": "Databricks",
    "hackerone": "HackerOne",
    "dragos": "Dragos",
}

# Companies using Lever ATS (verified slugs)
# To find a slug: visit jobs.lever.co/<slug> — if it loads, it's valid.
LEVER_COMPANIES = {}

# Companies with custom career pages (requires CSS selectors).
# Note: These may break if the company redesigns their site.
# IBM and Cisco use JavaScript-rendered pages — results may be empty
# without a headless browser (Selenium/Playwright).
CUSTOM_COMPANIES = [
    {
        "name": "Cisco",
        "url": "https://jobs.cisco.com/jobs/SearchJobs/cybersecurity?21178=%5B169482%5D&21178_format=6020&listFilterMode=1",
        "base_url": "https://jobs.cisco.com",
        "job_selector": "article.job-tile",
        "title_selector": "h2.job-title",
        "link_selector": "a",
        "location_selector": ".job-location",
    },
    {
        "name": "IBM",
        "url": "https://www.ibm.com/employment/#jobs?field_keyword_08[]=Cybersecurity&field_keyword_05[]=Entry+Level",
        "base_url": "https://www.ibm.com",
        "job_selector": ".bx--tile",
        "title_selector": "h3",
        "link_selector": "a",
        "location_selector": ".job-location",
    },
    # Add more custom companies here following the same format
]
