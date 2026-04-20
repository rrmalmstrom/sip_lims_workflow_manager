#!/usr/bin/env python3
"""
Mock NO_SNAPSHOT_ITEMS script for first.FA.output.analysis.py
Used in SIP workflow integration tests (Scenario 10).

This variant simulates a script that is missing the SNAPSHOT_ITEMS variable
entirely. The workflow manager should detect this and abort before running
the script.
"""

# NOTE: SNAPSHOT_ITEMS is intentionally absent to test abort behavior.

import sys
from pathlib import Path


def create_success_marker():
    """Create success marker file for workflow manager integration."""
    marker = Path(".step_complete")
    marker.write_text("success\n")


def main():
    project_dir = Path.cwd()

    fa_dir = project_dir / "4_make_library_analyze_fa" / "B_first_attempt_fa_result"
    fa_dir.mkdir(parents=True, exist_ok=True)
    (fa_dir / "thresholds.txt").write_text("mock thresholds\n")
    (fa_dir / "fa_results.csv").write_text("mock FA results\n")

    create_success_marker()


if __name__ == "__main__":
    main()
