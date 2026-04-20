#!/usr/bin/env python3
"""
Mock script for run.pooling.preparation.py
Used in SIP workflow integration tests.

SNAPSHOT_ITEMS declares the files this script modifies (pre-existing files
that need to be snapshotted before the script runs).
"""

SNAPSHOT_ITEMS = [
    "lib_info_submitted_to_clarity.db",
    "lib_info_submitted_to_clarity.csv",
    "5_pooling/C_assign_libs_to_pools/assign_pool_number_sheet.xlsx",
]

import sys
from pathlib import Path


def create_success_marker():
    """Create success marker file for workflow manager integration."""
    marker = Path(".step_complete")
    marker.write_text("success\n")


def main():
    project_dir = Path.cwd()

    # Simulate creating output files
    (project_dir / "lib_info_submitted_to_clarity.db").write_text("mock db\n")
    (project_dir / "lib_info_submitted_to_clarity.csv").write_text("mock csv\n")

    pooling_dir = project_dir / "5_pooling"
    pooling_dir.mkdir(parents=True, exist_ok=True)

    assign_dir = pooling_dir / "C_assign_libs_to_pools"
    assign_dir.mkdir(parents=True, exist_ok=True)
    (assign_dir / "assign_pool_number_sheet.xlsx").write_text("mock xlsx\n")

    (pooling_dir / "pool_summary.csv").write_text("mock pool summary\n")

    attempt_dir = pooling_dir / "E_pooling_and_rework" / "Attempt_1"
    attempt_dir.mkdir(parents=True, exist_ok=True)
    (attempt_dir / "hamilton_transfer.csv").write_text("mock hamilton transfer\n")

    create_success_marker()


if __name__ == "__main__":
    main()
