#!/usr/bin/env python3
"""
Mock script for SIP Step 10: Second Attempt Library Creation.

SNAPSHOT_ITEMS: project_database.db, project_database.csv, lib_info.db, lib_info.csv.
New output files in C_second_attempt_make_lib/ and D_second_attempt_fa_result/thresholds.txt
are newly created — manifest diff handles them.
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
    (status_dir / "rework.first.attempt.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "project_database.db").write_text("mock sip project_database - step 10\n")
    (base_dir / "project_database.csv").write_text("sample_id,fraction,lib_plate,rework\nSIP001,F1,LP001,yes\n")
    (base_dir / "lib_info.db").write_text("mock sip lib_info - step 10\n")
    (base_dir / "lib_info.csv").write_text("lib_id,sample_id,lib_plate,rework\nL001,SIP001,LP001,yes\n")

    rework_dir = base_dir / "4_make_library_analyze_fa" / "C_second_attempt_make_lib"
    rework_dir.mkdir(parents=True, exist_ok=True)
    (rework_dir / "echo_transfer_file_2nd.csv").write_text("source,dest,vol\nA1,B1,100\n")

    fa2_dir = base_dir / "4_make_library_analyze_fa" / "D_second_attempt_fa_result"
    fa2_dir.mkdir(parents=True, exist_ok=True)
    (fa2_dir / "thresholds.txt").write_text("lower=100\nupper=1000\n")

    create_success_marker()
    print("Mock SIP step 10 (rework_first_attempt) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
