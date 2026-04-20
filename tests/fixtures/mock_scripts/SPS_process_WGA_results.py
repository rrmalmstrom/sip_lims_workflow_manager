#!/usr/bin/env python3
"""
Mock script for SPS-CE Step 2: Process WGA Results.

SNAPSHOT_ITEMS is empty — this script only creates new files.
The manifest diff handles cleanup on rollback.
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = []
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    (status_dir / "SPS_process_WGA_results.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    wga_dir = base_dir / "2_sort_plates_and_amplify_genomes" / "B_WGA_results"
    wga_dir.mkdir(parents=True, exist_ok=True)
    (wga_dir / "summary_WGA_results.csv").write_text(
        "plate_id,passing_wells\nP001,350\n"
    )

    create_success_marker()
    print("Mock SPS step 2 (process_wga_results) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
