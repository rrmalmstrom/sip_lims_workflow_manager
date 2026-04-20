#!/usr/bin/env python3
"""
Mock script for SIP Step 17: Generate Pool Assignment Tool.

SNAPSHOT_ITEMS = [] — only creates new files (assign_pool_number_sheet.xlsx).
The manifest diff handles cleanup on rollback.
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = []
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    (status_dir / "generate_pool_assignment_tool.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    pool_dir = base_dir / "5_pooling" / "C_assign_libs_to_pools"
    pool_dir.mkdir(parents=True, exist_ok=True)
    (pool_dir / "assign_pool_number_sheet.xlsx").write_text("mock pool assignment xlsx\n")

    create_success_marker()
    print("Mock SIP step 17 (generate_pool_tool) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
