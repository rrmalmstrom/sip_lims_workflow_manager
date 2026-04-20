#!/usr/bin/env python3
"""
Mock FAILING script for first.FA.output.analysis.py
Used in SIP workflow integration tests (Scenarios 3 and 11).

This variant simulates a script that fails mid-run:
- Does NOT create a success marker
- Exits with code 1
"""

SNAPSHOT_ITEMS = [
    "4_make_library_analyze_fa/B_first_attempt_fa_result/thresholds.txt",
]

import sys
from pathlib import Path


def main():
    project_dir = Path.cwd()

    # Simulate partial work before failure
    fa_dir = project_dir / "4_make_library_analyze_fa" / "B_first_attempt_fa_result"
    fa_dir.mkdir(parents=True, exist_ok=True)
    (fa_dir / "partial_output.csv").write_text("partial output before failure\n")

    # Simulate failure — no success marker, exit 1
    print("ERROR: Simulated FA analysis failure", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
