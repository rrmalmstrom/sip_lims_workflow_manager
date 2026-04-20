#!/usr/bin/env python3
"""
Mock script for rework.pooling.steps.py
Used in SIP workflow integration tests.

SNAPSHOT_ITEMS declares the files this script modifies (pre-existing files
that need to be snapshotted before the script runs).
"""

SNAPSHOT_ITEMS = [
    "5_pooling/pool_summary.csv",
    "lib_info_submitted_to_clarity.db",
    "lib_info_submitted_to_clarity.csv",
]

import sys
from pathlib import Path


def create_success_marker():
    """Create success marker file for workflow manager integration."""
    marker = Path(".step_complete")
    marker.write_text("success\n")


def main():
    project_dir = Path.cwd()

    # Simulate updating pool summary and lib info files
    pooling_dir = project_dir / "5_pooling"
    pooling_dir.mkdir(parents=True, exist_ok=True)
    (pooling_dir / "pool_summary.csv").write_text("mock pool summary after rework\n")

    (project_dir / "lib_info_submitted_to_clarity.db").write_text("mock db after rework\n")
    (project_dir / "lib_info_submitted_to_clarity.csv").write_text("mock csv after rework\n")

    # Simulate creating rework output files
    rework_dir = pooling_dir / "E_pooling_and_rework" / "Attempt_2"
    rework_dir.mkdir(parents=True, exist_ok=True)
    (rework_dir / "hamilton_transfer.csv").write_text("mock rework hamilton transfer\n")

    create_success_marker()


if __name__ == "__main__":
    main()
