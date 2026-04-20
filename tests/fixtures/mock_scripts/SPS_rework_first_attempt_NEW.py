#!/usr/bin/env python3
"""
Mock script for SPS-CE Step 7: Rework First Attempt.

SNAPSHOT_ITEMS: project_summary.db, master_plate_data.csv.
Output files in C_second_attempt_make_lib/ and D_second_attempt_fa_result/
are newly created — manifest diff handles them.
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
    (status_dir / "SPS_rework_first_attempt_NEW.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "project_summary.db").write_text("mock sps db content - step 7\n")
    (base_dir / "master_plate_data.csv").write_text(
        "plate_id,lib_plate,index,rework\nP001,LP001,i701,yes\n"
    )

    rework_dir = base_dir / "3_make_library_analyze_fa" / "C_second_attempt_make_lib"
    rework_dir.mkdir(parents=True, exist_ok=True)
    (rework_dir / "illumina_index_file_2nd.csv").write_text(
        "sample_id,index\nS001,i702\n"
    )

    fa2_dir = base_dir / "3_make_library_analyze_fa" / "D_second_attempt_fa_result"
    fa2_dir.mkdir(parents=True, exist_ok=True)
    (fa2_dir / "thresholds.txt").write_text("lower=100\nupper=1000\n")

    create_success_marker()
    print("Mock SPS step 7 (rework_first_attempt) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
