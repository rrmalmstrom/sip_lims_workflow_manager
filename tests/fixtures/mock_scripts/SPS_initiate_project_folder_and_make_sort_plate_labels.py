#!/usr/bin/env python3
"""
Mock script for SPS-CE Step 1: Initiate Project and Make Sort Plate Labels.

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
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    marker = status_dir / "SPS_initiate_project_folder_and_make_sort_plate_labels.success"
    marker.write_text("success")


def main():
    base_dir = Path(os.getcwd())

    # Create/update SNAPSHOT_ITEMS files
    (base_dir / "project_summary.db").write_text("mock sps db content - step 1\n")
    (base_dir / "sample_metadata.csv").write_text("plate_id,sample_name\nP001,Sample1\n")
    (base_dir / "individual_plates.csv").write_text("plate_id,barcode\nP001,BC001\n")

    # Create folder structure (empty dirs)
    for d in [
        "1_make_barcode_labels/bartender_barcode_labels",
        "1_make_barcode_labels/previously_process_label_input_files/custom_plates",
        "1_make_barcode_labels/previously_process_label_input_files/standard_plates",
        "2_sort_plates_and_amplify_genomes/A_sort_plate_layouts",
        "2_sort_plates_and_amplify_genomes/B_WGA_results",
        "3_make_library_analyze_fa",
        "4_pooling",
        "archived_files",
        "MISC",
    ]:
        (base_dir / d).mkdir(parents=True, exist_ok=True)

    # Create a barcode label file
    bartender_dir = base_dir / "1_make_barcode_labels" / "bartender_barcode_labels"
    (bartender_dir / "BARTENDER_sort_plate_labels.txt").write_text("mock bartender labels\n")

    create_success_marker()
    print("Mock SPS step 1 (initiate_project) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
