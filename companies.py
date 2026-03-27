"""
Company configurations.

GREENHOUSE_COMPANIES: {greenhouse_board_id: display_name}
LEVER_COMPANIES:      {lever_company_slug: display_name}
CUSTOM_COMPANIES:     list of dicts with CSS selector configs
"""

# Companies using Greenhouse ATS (public API available)
GREENHOUSE_COMPANIES = {
    "crowdstrike": "CrowdStrike",
    "paloaltonetworks": "Palo Alto Networks",
    "gitlab": "GitLab",
    "cloudflare": "Cloudflare",
    "okta": "Okta",
    "sentinelone": "SentinelOne",
    "lacework": "Lacework",
    "huntress": "Huntress",
    "tenable": "Tenable",
}

# Companies using Lever ATS (public API available)
LEVER_COMPANIES = {
    "rapid7": "Rapid7",
    "dragos": "Dragos",
    "darktrace": "Darktrace",
    "recordedfuture": "Recorded Future",
    "exabeam": "Exabeam",
}

# Companies with custom career pages (requires CSS selectors)
# Note: These may break if the company redesigns their site.
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
