"""
Save scraped job results to CSV and JSON.
"""

import csv
import json
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("results")


def save_results(jobs: list[dict]) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    json_path = OUTPUT_DIR / f"jobs_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(jobs, f, indent=2)
    print(f"[+] Saved JSON -> {json_path}")

    csv_path = OUTPUT_DIR / f"jobs_{timestamp}.csv"
    if jobs:
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
            writer.writeheader()
            writer.writerows(jobs)
        print(f"[+] Saved CSV  -> {csv_path}")
