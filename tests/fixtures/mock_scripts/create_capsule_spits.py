#!/usr/bin/env python3
"""
Mock script for Step 4: Create SPITS file.

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
    "4_plate_selection_and_pooling/",
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    marker = status_dir / "create_capsule_spits.success"
    marker.write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "project_summary.db").write_text("mock db content - step 4\n")
    (base_dir / "master_plate_data.csv").write_text("plate_id,selected\nP001,YES\n")
    (base_dir / "individual_plates.csv").write_text("plate_id,barcode,selected\nP001,BC001,YES\n")

    pooling_dir = base_dir / "4_plate_selection_and_pooling"
    pooling_dir.mkdir(exist_ok=True)
    (pooling_dir / "plate_selection.csv").write_text("plate_id,index_set\nP001,SET1\n")
    (pooling_dir / "spits_file.csv").write_text("sample_name,index\nSample1,ATCG\n")

    create_success_marker()
    print("Mock step 4 (select_plates) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
