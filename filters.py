"""
Keyword filters to identify entry-level cybersecurity jobs.
"""

import re

# Multi-word or unambiguous keywords - plain substring match is fine
CYBERSECURITY_KEYWORDS_PLAIN = [
    "cyber", "security", "infosec", "penetration", "pentest",
    "vulnerability", "threat", "incident response", "forensic",
    "siem", "firewall", "devsecops", "appsec", "cloud security",
    "network security", "security analyst", "security engineer",
    "security operations",
]

# Short acronyms that need word-boundary matching to avoid false substring hits
CYBERSECURITY_KEYWORDS_WORD_BOUNDARY = [
    "soc", "iam", "grc",
]

# Generic terms that only count when paired with a security context
SECURITY_CONTEXT_KEYWORDS = [
    "compliance", "risk", "identity",
]

SECURITY_CONTEXT_QUALIFIERS = [
    "cyber", "security", "information", "infosec", "cloud",
]

ENTRY_LEVEL_KEYWORDS = [
    "entry level", "entry-level", "junior", "new grad", "new graduate",
    "early career", "intern", "internship", "apprentice", "trainee",
    "level i", "tier i", "tier 1",
]

ASSOCIATE_SECURITY_QUALIFIERS = [
    "security", "cyber", "analyst", "engineer", "soc", "grc",
]

SENIOR_EXCLUSION_KEYWORDS = [
    "senior", "staff", "principal", "lead", "manager",
    "director", "vp ", "head of", "architect", "fellow",
    "sr.", "sr ",
]

# Explicit mid/senior level number suffixes — exclude these
MID_SENIOR_LEVEL_PATTERNS = [
    r"\bii\b", r"\biii\b", r"\biv\b",         # Roman numerals II+
    r"\blevel [2-9]\b", r"\blevel 1[0-9]\b",   # Level 2+
    r"\bgrade [2-9]\b",                         # Grade 2+
    r"\b[2-9]\b$",                              # Trailing lone digit 2–9
    r"senior", r" sr[\. ]",                     # Redundant but explicit
]

NON_CYBER_EXCLUSION_KEYWORDS = [
    "billing", "marketing", "sales", "gtm ", "finance", "payroll",
    "commission", "legal operations", "field enablement", "data center services",
    "business systems", "reporting analyst", "product analyst",
    "application development analyst",
    # Physical / facility security (not cybersecurity)
    "security guard", "security associate", "security officer, physical",
    "facility security", "industrial security", "personnel security",
    "physical security", "program security officer", "contract program security",
    "contractor program security", "overnight security", "outside security",
    "asset security executive", "administrative business partner",
    "security cooperation", "security assistance",
]


def is_cybersecurity(title):
    t = title.lower()

    if any(kw in t for kw in NON_CYBER_EXCLUSION_KEYWORDS):
        return False

    if any(kw in t for kw in CYBERSECURITY_KEYWORDS_PLAIN):
        return True

    if any(re.search(r"\b" + re.escape(kw) + r"\b", t) for kw in CYBERSECURITY_KEYWORDS_WORD_BOUNDARY):
        return True

    for kw in SECURITY_CONTEXT_KEYWORDS:
        if kw in t and any(q in t for q in SECURITY_CONTEXT_QUALIFIERS):
            return True

    return False


def is_entry_level(title, description=""):
    combined = (title + " " + description).lower()
    t = title.lower()

    # Exclude anything with an explicit senior/lead/manager indicator
    if any(kw in t for kw in SENIOR_EXCLUSION_KEYWORDS):
        return False

    # Exclude mid/senior level number patterns (II, III, Level 2, etc.)
    if any(re.search(p, t) for p in MID_SENIOR_LEVEL_PATTERNS):
        return False

    # Explicit entry-level markers are a strong positive signal
    if any(kw in combined for kw in ENTRY_LEVEL_KEYWORDS):
        return True

    # "Associate" + security context is entry-level
    if "associate" in t and any(q in t for q in ASSOCIATE_SECURITY_QUALIFIERS):
        return True

    # No explicit level indicator at all → assume entry/mid, include it.
    # Users would rather see a "Cybersecurity Analyst" that turns out to be
    # mid-level than miss a genuine entry-level role with no label.
    return True
