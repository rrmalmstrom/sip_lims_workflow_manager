#!/usr/bin/env python3
"""
Mock script for Step 3: Analyze FA data.

Simulates what the real script does:
  - Creates/modifies SNAPSHOT_ITEMS files
  - Writes a success marker
  - Exits with code 0
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


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    marker = status_dir / "capsule_fa_analysis.success"
    marker.write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "project_summary.db").write_text("mock db content - step 3\n")
    (base_dir / "master_plate_data.csv").write_text("plate_id,fa_result\nP001,PASS\n")
    (base_dir / "individual_plates.csv").write_text("plate_id,barcode,fa_status\nP001,BC001,PASS\n")

    fa_dir = base_dir / "3_FA_analysis"
    fa_dir.mkdir(exist_ok=True)
    (fa_dir / "fa_summary.csv").write_text("plate_id,avg_size,result\nP001,450,PASS\n")
    (fa_dir / "fa_visualization.pdf").write_text("%PDF-1.4 mock pdf\n")
    (fa_dir / "thresholds.txt").write_text("lower=200\nupper=800\n")

    create_success_marker()
    print("Mock step 3 (analyze_quality) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
