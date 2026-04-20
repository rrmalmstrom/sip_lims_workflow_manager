#!/usr/bin/env python3
"""
Mock script for SIP Step 15: Conclude FA Analysis.

SNAPSHOT_ITEMS: lib_info.db, lib_info.csv.
New final_lib_summary.csv in 5_pooling/A_make_clarity_aliquot_upload_file/ is newly created.
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = [
    "lib_info.db",
    "lib_info.csv",
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    (status_dir / "conclude.all.fa.analysis.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "lib_info.db").write_text("mock sip lib_info - step 15 final\n")
    (base_dir / "lib_info.csv").write_text("lib_id,sample_id,final_pass\nL001,SIP001,yes\n")

    clarity_dir = base_dir / "5_pooling" / "A_make_clarity_aliquot_upload_file"
    clarity_dir.mkdir(parents=True, exist_ok=True)
    (clarity_dir / "final_lib_summary.csv").write_text("lib_id,conc,pass\nL001,12.5,yes\n")

    create_success_marker()
    print("Mock SIP step 15 (conclude_fa_analysis) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
