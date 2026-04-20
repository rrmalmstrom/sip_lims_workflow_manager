#!/usr/bin/env python3
"""
Mock script for SIP Step 8: Create Library Files (Condensed Plates).

SNAPSHOT_ITEMS: project_database.db, project_database.csv, lib_info.db, lib_info.csv.
New output files in 4_make_library_analyze_fa/A_first_attempt_make_lib/ are newly created.
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = [
    "project_database.db",
    "project_database.csv",
    "lib_info.db",
    "lib_info.csv",
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    (status_dir / "make.library.creation.files.condensed.plates.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "project_database.db").write_text("mock sip project_database - step 8\n")
    (base_dir / "project_database.csv").write_text("sample_id,fraction,lib_plate\nSIP001,F1,LP001\n")
    (base_dir / "lib_info.db").write_text("mock sip lib_info - step 8\n")
    (base_dir / "lib_info.csv").write_text("lib_id,sample_id,lib_plate\nL001,SIP001,LP001\n")

    make_lib_dir = base_dir / "4_make_library_analyze_fa" / "A_first_attempt_make_lib"
    make_lib_dir.mkdir(parents=True, exist_ok=True)
    (make_lib_dir / "echo_transfer_file.csv").write_text("source,dest,vol\nA1,B1,100\n")
    (make_lib_dir / "illumina_index_file.csv").write_text("sample_id,index\nL001,i701\n")

    fa_result_dir = base_dir / "4_make_library_analyze_fa" / "B_first_attempt_fa_result"
    fa_result_dir.mkdir(parents=True, exist_ok=True)
    (fa_result_dir / "thresholds.txt").write_text("lower=100\nupper=1000\n")

    create_success_marker()
    print("Mock SIP step 8 (make_library_condensed) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
