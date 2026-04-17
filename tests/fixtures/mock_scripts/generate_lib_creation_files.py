#!/usr/bin/env python3
"""
Mock script for Step 2: Generate Lib Creation Files.

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
    "2_library_creation/",
    "3_FA_analysis/thresholds.txt",
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    marker = status_dir / "generate_lib_creation_files.success"
    marker.write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "project_summary.db").write_text("mock db content - step 2\n")
    (base_dir / "master_plate_data.csv").write_text("plate_id,library_id\nP001,LIB001\n")
    (base_dir / "individual_plates.csv").write_text("plate_id,barcode,library\nP001,BC001,LIB001\n")

    lib_dir = base_dir / "2_library_creation"
    lib_dir.mkdir(exist_ok=True)
    (lib_dir / "illumina_index_file.csv").write_text("index_id,sequence\nI001,ATCG\n")
    (lib_dir / "fa_transfer_file.csv").write_text("well,volume\nA01,10\n")

    fa_dir = base_dir / "3_FA_analysis"
    fa_dir.mkdir(exist_ok=True)
    (fa_dir / "thresholds.txt").write_text("lower=200\nupper=800\n")

    create_success_marker()
    print("Mock step 2 (prep_library) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
