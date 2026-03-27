"""
Verify a Workday company config before adding it to workday.py.

Usage:
  python verify_workday.py <tenant> <wdN> <site_path>

Examples:
  python verify_workday.py crowdstrike wd5 crowdstrikecareers   # known good
  python verify_workday.py boozallen wd1 EXP
  python verify_workday.py paloaltonetworks wd1 PaloAltoNetworksCareers

How to find the correct values:
  1. Visit the company's careers page (e.g. careers.boozallen.com)
  2. It will load or redirect to a Workday URL:
       https://<tenant>.<wdN>.myworkdayjobs.com/<site_path>/...
  3. Copy those three values and run this script.
"""

import sys
import requests

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def verify(tenant, wd_num, site):
    base_url = f"https://{tenant}.{wd_num}.myworkdayjobs.com/{site}"
    api_url = f"https://{tenant}.{wd_num}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"

    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})

    print(f"[1] GET {base_url}")
    try:
        r = session.get(base_url, timeout=15)
        print(f"    Status: {r.status_code}")
        if r.status_code != 200:
            print(f"    FAIL: site path '{site}' returned {r.status_code}. Try a different site name.")
            return
    except Exception as e:
        print(f"    FAIL: {e}")
        return

    csrf = session.cookies.get("XSRF-TOKEN", "")
    print(f"    CSRF token: {repr(csrf) if csrf else '(none)'}")

    post_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Origin": f"https://{tenant}.{wd_num}.myworkdayjobs.com",
        "Referer": base_url,
    }
    if csrf:
        post_headers["X-XSRF-TOKEN"] = csrf

    print(f"[2] POST {api_url}")
    payload = {"appliedFacets": {}, "limit": 5, "offset": 0, "searchText": "security"}
    try:
        r = session.post(api_url, headers=post_headers, json=payload, timeout=15)
        print(f"    Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            total = data.get("total", 0)
            sample = [j.get("title") for j in data.get("jobPostings", [])[:3]]
            print(f"    OK — {total} total jobs. Sample titles: {sample}")
            print(f"\nAdd to WORKDAY_COMPANIES in workday.py:")
            print(f'    "{tenant.title()}": ("{tenant}", "{wd_num}", "{site}"),')
        else:
            print(f"    FAIL: {r.text[:200]}")
    except Exception as e:
        print(f"    FAIL: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python verify_workday.py <tenant> <wdN> <site_path>")
        print("Example: python verify_workday.py crowdstrike wd5 crowdstrikecareers")
        sys.exit(1)

    verify(sys.argv[1], sys.argv[2], sys.argv[3])
