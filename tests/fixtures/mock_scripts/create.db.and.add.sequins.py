#!/usr/bin/env python3
"""
Mock script for SIP Step 4: Create DB and Add Sequins.

SNAPSHOT_ITEMS: lib_info.db, lib_info.csv.
New sequin transfer files are newly created — manifest diff handles them.
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
    (status_dir / "create.db.and.add.sequins.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "lib_info.db").write_text("mock sip lib_info - step 4\n")
    (base_dir / "lib_info.csv").write_text("lib_id,sample_id,fraction\nL001,SIP001,F1\n")

    sequin_dir = base_dir / "3_merge_density_vol_conc_files" / "sequins" / "sequin_transfer_files_run1"
    sequin_dir.mkdir(parents=True, exist_ok=True)
    (sequin_dir / "sequin_SIP001.csv").write_text("well,vol\nA1,2.5\n")

    create_success_marker()
    print("Mock SIP step 4 (create_db_sequins) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
