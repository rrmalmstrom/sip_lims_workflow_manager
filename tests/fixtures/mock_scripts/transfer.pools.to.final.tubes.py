#!/usr/bin/env python3
"""
Mock script for transfer.pools.to.final.tubes.py
Used in SIP workflow integration tests.

SNAPSHOT_ITEMS declares the files this script modifies (pre-existing files
that need to be snapshotted before the script runs).
"""

SNAPSHOT_ITEMS = [
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

    # Simulate updating lib info files with final tube transfer data
    (project_dir / "lib_info_submitted_to_clarity.db").write_text("mock db after final transfer\n")
    (project_dir / "lib_info_submitted_to_clarity.csv").write_text("mock csv after final transfer\n")

    # Simulate creating final tube transfer output files
    pooling_dir = project_dir / "5_pooling"
    pooling_dir.mkdir(parents=True, exist_ok=True)

    final_dir = pooling_dir / "F_transfer_to_final_tubes"
    final_dir.mkdir(parents=True, exist_ok=True)
    (final_dir / "final_tube_transfer.csv").write_text("mock final tube transfer\n")
    (final_dir / "qpcr_file.csv").write_text("mock qpcr file\n")

    create_success_marker()


if __name__ == "__main__":
    main()
