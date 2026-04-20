#!/usr/bin/env python3
"""
Mock script for SIP Step 2: Create Ultracentrifuge Tubes.

SNAPSHOT_ITEMS: project_database.db, project_database.csv.
New output files in 2_load_ultracentrifuge/ are newly created — manifest diff handles them.
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = [
    "project_database.db",
    "project_database.csv",
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    (status_dir / "ultracentrifuge.transfer.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "project_database.db").write_text("mock sip project_database - step 2\n")
    (base_dir / "project_database.csv").write_text("sample_id,fraction,tube\nSIP001,F1,T001\n")

    hamilton_dir = base_dir / "2_load_ultracentrifuge" / "Hamilton_transfer_files"
    hamilton_dir.mkdir(parents=True, exist_ok=True)
    (hamilton_dir / "Ultracentrifuge_transfer_SIP001.csv").write_text(
        "source,dest,vol\nA1,T001,500\n"
    )

    bartender_dir = base_dir / "2_load_ultracentrifuge" / "BARTENDER_files"
    bartender_dir.mkdir(parents=True, exist_ok=True)
    (bartender_dir / "BARTENDER_ultracentrifuge_tube_labels.txt").write_text(
        "mock tube labels\n"
    )

    create_success_marker()
    print("Mock SIP step 2 (ultracentrifuge_transfer) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
