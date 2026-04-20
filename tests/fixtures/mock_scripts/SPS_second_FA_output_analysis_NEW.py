#!/usr/bin/env python3
"""
Mock script for SPS-CE Step 8: Second FA Output Analysis.

SNAPSHOT_ITEMS is empty — this script only creates new files.
FA archive is a PERMANENT_EXCLUSION — not listed here.
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
    (status_dir / "SPS_second_FA_output_analysis_NEW.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    fa2_dir = base_dir / "3_make_library_analyze_fa" / "D_second_attempt_fa_result"
    fa2_dir.mkdir(parents=True, exist_ok=True)
    (fa2_dir / "reduced_2nd_fa_analysis_summary.txt").write_text(
        "passed=280\nfailed=20\n"
    )
    (fa2_dir / "double_failed_libraries.txt").write_text("S042\nS099\n")

    create_success_marker()
    print("Mock SPS step 8 (second_fa_analysis) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
