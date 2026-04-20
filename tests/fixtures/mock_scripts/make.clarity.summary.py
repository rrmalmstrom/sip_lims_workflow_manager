#!/usr/bin/env python3
"""
Mock script for SIP Step 16: Make Clarity Summary.

SNAPSHOT_ITEMS: lib_info.db, lib_info.csv,
  5_pooling/A_make_clarity_aliquot_upload_file/final_lib_summary.csv.
New outputs (lib_info_submitted_to_clarity.db/csv, clarity_summary.xlsx) are newly created.
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = [
    "lib_info.db",
    "lib_info.csv",
    "5_pooling/A_make_clarity_aliquot_upload_file/final_lib_summary.csv",
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    (status_dir / "make.clarity.summary.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "lib_info.db").write_text("mock sip lib_info - step 16\n")
    (base_dir / "lib_info.csv").write_text("lib_id,sample_id,final_pass\nL001,SIP001,yes\n")

    clarity_dir = base_dir / "5_pooling" / "A_make_clarity_aliquot_upload_file"
    clarity_dir.mkdir(parents=True, exist_ok=True)
    (clarity_dir / "final_lib_summary.csv").write_text("lib_id,conc,pass\nL001,12.5,yes\n")
    (clarity_dir / "clarity_summary.xlsx").write_text("mock xlsx\n")

    (base_dir / "lib_info_submitted_to_clarity.db").write_text("mock clarity db\n")
    (base_dir / "lib_info_submitted_to_clarity.csv").write_text(
        "lib_id,sample_id,submitted\nL001,SIP001,yes\n"
    )

    create_success_marker()
    print("Mock SIP step 16 (make_clarity_summary) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
