"""
Keyword filters to identify entry-level cybersecurity jobs.
"""

CYBERSECURITY_KEYWORDS = [
    "cyber", "security", "infosec", "soc", "analyst",
    "penetration", "pentest", "vulnerability", "threat",
    "incident response", "forensic", "siem", "firewall",
    "identity", "iam", "compliance", "risk", "grc",
    "devsecops", "appsec", "cloud security", "network security",
]

ENTRY_LEVEL_KEYWORDS = [
    "entry level", "entry-level", "junior", "associate",
    "new grad", "new graduate", "graduate", "early career",
    "intern", "internship", "apprentice", "trainee", "i ", "level i",
]

# Titles that suggest senior roles — used to exclude false positives
SENIOR_EXCLUSION_KEYWORDS = [
    "senior", "staff", "principal", "lead", "manager",
    "director", "vp ", "head of", "architect", "fellow",
    "sr.", "sr ",
]


def is_cybersecurity(title: str) -> bool:
    title_lower = title.lower()
    return any(kw in title_lower for kw in CYBERSECURITY_KEYWORDS)


def is_entry_level(title: str, description: str = "") -> bool:
    combined = (title + " " + description).lower()
    title_lower = title.lower()

    # Reject clearly senior titles
    if any(kw in title_lower for kw in SENIOR_EXCLUSION_KEYWORDS):
        return False

    # Accept if entry-level keyword found in title or description
    return any(kw in combined for kw in ENTRY_LEVEL_KEYWORDS)
