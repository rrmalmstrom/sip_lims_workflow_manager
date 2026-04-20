#!/usr/bin/env python3
"""
Mock script for pool.FA12.analysis.py
Used in SIP workflow integration tests.

SNAPSHOT_ITEMS declares the files this script modifies (pre-existing files
that need to be snapshotted before the script runs).
"""

SNAPSHOT_ITEMS = [
    "5_pooling/pool_summary.csv",
]

import sys
from pathlib import Path


def create_success_marker():
    """Create success marker file for workflow manager integration."""
    marker = Path(".step_complete")
    marker.write_text("success\n")


def main():
    project_dir = Path.cwd()

    # Simulate updating pool_summary.csv with FA12 analysis results
    pooling_dir = project_dir / "5_pooling"
    pooling_dir.mkdir(parents=True, exist_ok=True)
    (pooling_dir / "pool_summary.csv").write_text("mock pool summary with FA12 results\n")

    # Simulate creating FA12 analysis output files
    fa12_dir = pooling_dir / "B_pool_FA12_analysis"
    fa12_dir.mkdir(parents=True, exist_ok=True)
    (fa12_dir / "pool_fa12_results.csv").write_text("mock FA12 results\n")

    create_success_marker()


if __name__ == "__main__":
    main()
