#!/usr/bin/env python3
"""
Mock script for Step 1: Initiate Project / Make Sort Labels.

Simulates what the real script does:
  - Creates/modifies SNAPSHOT_ITEMS files
  - Writes a success marker
  - Exits with code 0

IMPORTANT: SNAPSHOT_ITEMS must be present — parse_snapshot_items_from_script()
reads this variable before the script runs. Without it, run_step() aborts.
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = [
    "project_summary.db",
    "sample_metadata.csv",
    "individual_plates.csv",
    "1_make_barcode_labels/",
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    """Create success marker file for workflow manager integration."""
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    marker = status_dir / "initiate_project_folder_and_make_sort_plate_labels.success"
    marker.write_text("success")


def main():
    base_dir = Path(os.getcwd())

    # Create/update SNAPSHOT_ITEMS files
    (base_dir / "project_summary.db").write_text("mock db content - step 1\n")
    (base_dir / "sample_metadata.csv").write_text("plate_id,sample_name\nP001,Sample1\n")
    (base_dir / "individual_plates.csv").write_text("plate_id,barcode\nP001,BC001\n")

    labels_dir = base_dir / "1_make_barcode_labels"
    labels_dir.mkdir(exist_ok=True)
    (labels_dir / "sort_plate_labels.csv").write_text("label_id,barcode\nL001,BC001\n")
    (labels_dir / "bartender_labels.csv").write_text("barcode,plate\nBC001,P001\n")

    create_success_marker()
    print("Mock step 1 (init_project) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
