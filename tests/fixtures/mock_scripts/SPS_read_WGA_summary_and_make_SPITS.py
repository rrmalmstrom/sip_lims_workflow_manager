#!/usr/bin/env python3
"""
Mock script for SPS-CE Step 3: Read WGA Summary and Make SPITS.

SNAPSHOT_ITEMS: project_summary.db (modified in-place).
master_plate_data.csv and SPITS CSV are newly created — manifest diff handles them.
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = [
    "project_summary.db",
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    (status_dir / "SPS_read_WGA_summary_and_make_SPITS.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "project_summary.db").write_text("mock sps db content - step 3\n")
    (base_dir / "master_plate_data.csv").write_text("plate_id,lib_plate\nP001,LP001\n")

    wga_dir = base_dir / "2_sort_plates_and_amplify_genomes" / "B_WGA_results"
    wga_dir.mkdir(parents=True, exist_ok=True)
    (wga_dir / "SPITS_file.csv").write_text("sample_id,destination\nS001,LP001-A1\n")

    create_success_marker()
    print("Mock SPS step 3 (read_wga_and_make_spits) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
