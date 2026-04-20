#!/usr/bin/env python3
"""
Mock script for SIP Step 6: Generate CsCl Cleanup Files.

SNAPSHOT_ITEMS: lib_info.db, lib_info.csv.
New transfer files in CsCl_cleanup_info/Transfer_files_{date}/ are newly created.
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
    (status_dir / "generate.CsCl.cleanup.files.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "lib_info.db").write_text("mock sip lib_info - step 6\n")
    (base_dir / "lib_info.csv").write_text("lib_id,sample_id,fraction,cleanup_vol\nL001,SIP001,F1,50\n")

    transfer_dir = (
        base_dir / "3_merge_density_vol_conc_files" / "CsCl_cleanup_info" / "Transfer_files_run1"
    )
    transfer_dir.mkdir(parents=True, exist_ok=True)
    (transfer_dir / "hamilton_cleanup_transfer.csv").write_text(
        "source,dest,vol\nT001,C001,50\n"
    )

    create_success_marker()
    print("Mock SIP step 6 (generate_cscl_cleanup) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
