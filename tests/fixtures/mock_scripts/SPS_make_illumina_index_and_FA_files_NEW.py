#!/usr/bin/env python3
"""
Mock script for SPS-CE Step 4: Make Library Creation Input Files.

SNAPSHOT_ITEMS: project_summary.db, master_plate_data.csv.
Output files in 3_make_library_analyze_fa/ are newly created — manifest diff handles them.
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = [
    "project_summary.db",
    "master_plate_data.csv",
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    (status_dir / "SPS_make_illumina_index_and_FA_files_NEW.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "project_summary.db").write_text("mock sps db content - step 4\n")
    (base_dir / "master_plate_data.csv").write_text("plate_id,lib_plate,index\nP001,LP001,i701\n")

    make_lib_dir = base_dir / "3_make_library_analyze_fa" / "A_first_attempt_make_lib"
    make_lib_dir.mkdir(parents=True, exist_ok=True)
    (make_lib_dir / "illumina_index_file.csv").write_text("sample_id,index\nS001,i701\n")
    (make_lib_dir / "fa_transfer_file.csv").write_text("source,dest,vol\nA1,B1,100\n")

    fa_result_dir = base_dir / "3_make_library_analyze_fa" / "B_first_attempt_fa_result"
    fa_result_dir.mkdir(parents=True, exist_ok=True)
    (fa_result_dir / "thresholds.txt").write_text("lower=100\nupper=1000\n")

    create_success_marker()
    print("Mock SPS step 4 (make_library_input_files) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
