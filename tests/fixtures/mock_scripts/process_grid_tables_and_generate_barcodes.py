#!/usr/bin/env python3
"""
Mock script for Step 5: Process Grid Tables & Generate Barcodes.

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
    marker = status_dir / "process_grid_tables_and_generate_barcodes.success"
    marker.write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "project_summary.db").write_text("mock db content - step 5\n")
    (base_dir / "master_plate_data.csv").write_text("plate_id,container_barcode\nP001,CB001\n")
    (base_dir / "individual_plates.csv").write_text("plate_id,barcode,container\nP001,BC001,CB001\n")

    pooling_dir = base_dir / "4_plate_selection_and_pooling"
    pooling_dir.mkdir(exist_ok=True)
    (pooling_dir / "grid_barcodes.csv").write_text("grid_position,barcode\nA01,CB001\n")
    (pooling_dir / "bartender_grid_file.csv").write_text("barcode,container\nCB001,P001\n")

    create_success_marker()
    print("Mock step 5 (process_grid_barcodes) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
