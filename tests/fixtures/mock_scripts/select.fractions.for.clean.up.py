#!/usr/bin/env python3
"""
Mock script for SIP Step 5: Select Fractions for Cleanup.

SNAPSHOT_ITEMS: project_database.db, project_database.csv, lib_info.db, lib_info.csv.
New output files in CsCl_cleanup_info/ are newly created — manifest diff handles them.
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
    (status_dir / "select.fractions.for.clean.up.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "project_database.db").write_text("mock sip project_database - step 5\n")
    (base_dir / "project_database.csv").write_text("sample_id,fraction,selected\nSIP001,F1,yes\n")
    (base_dir / "lib_info.db").write_text("mock sip lib_info - step 5\n")
    (base_dir / "lib_info.csv").write_text("lib_id,sample_id,fraction,selected\nL001,SIP001,F1,yes\n")

    cleanup_dir = base_dir / "3_merge_density_vol_conc_files" / "CsCl_cleanup_info"
    cleanup_dir.mkdir(parents=True, exist_ok=True)
    (cleanup_dir / "review_fractions_for_cleanup.csv").write_text(
        "lib_id,fraction,action\nL001,F1,keep\n"
    )

    create_success_marker()
    print("Mock SIP step 5 (select_fractions_cleanup) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
