#!/usr/bin/env python3
"""
FAILING mock script for Step 3: Analyze FA data.

Used by integration tests to simulate a script that:
  - Creates some output files (partial work)
  - Does NOT write a success marker
  - Exits with code 1

This triggers the automatic rollback path in handle_step_result().

IMPORTANT: SNAPSHOT_ITEMS must still be present — parse_snapshot_items_from_script()
reads this variable before the script runs.
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = [
    "project_summary.db",
    "master_plate_data.csv",
    "individual_plates.csv",
    "3_FA_analysis/",
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def main():
    base_dir = Path(os.getcwd())

    # Partially create output files (simulating a script that crashes mid-run)
    fa_dir = base_dir / "3_FA_analysis"
    fa_dir.mkdir(exist_ok=True)
    (fa_dir / "fa_summary_partial.csv").write_text("plate_id,avg_size\nP001,INCOMPLETE\n")

    # Intentionally do NOT write a success marker
    # Intentionally exit with non-zero code
    print("Mock step 3 FAILING — simulating script failure.")
    sys.exit(1)


if __name__ == "__main__":
    main()
