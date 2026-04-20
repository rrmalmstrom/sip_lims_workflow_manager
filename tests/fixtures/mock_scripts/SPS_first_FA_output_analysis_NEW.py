#!/usr/bin/env python3
"""
Mock script for SPS-CE Step 5: First FA Output Analysis.

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
    (status_dir / "SPS_first_FA_output_analysis_NEW.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    fa_result_dir = base_dir / "3_make_library_analyze_fa" / "B_first_attempt_fa_result"
    fa_result_dir.mkdir(parents=True, exist_ok=True)
    (fa_result_dir / "reduced_fa_analysis_summary.txt").write_text(
        "passed=300\nfailed=50\n"
    )
    (fa_result_dir / "fa_smear_plate1.csv").write_text(
        "sample_id,size_bp,conc\nS001,450,5.2\n"
    )

    create_success_marker()
    print("Mock SPS step 5 (first_fa_analysis) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
