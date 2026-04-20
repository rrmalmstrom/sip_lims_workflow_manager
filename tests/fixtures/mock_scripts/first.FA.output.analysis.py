#!/usr/bin/env python3
"""
Mock script for SIP Step 9: Analyze Library QC (1st FA).

SNAPSHOT_ITEMS: 4_make_library_analyze_fa/B_first_attempt_fa_result/thresholds.txt
(user-edited before this script runs — must be backed up).
FA archive goes to archived_files/FA_results_archive/first_lib_attempt_fa_results/
which is a PERMANENT_EXCLUSION — not listed here.
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = [
    "4_make_library_analyze_fa/B_first_attempt_fa_result/thresholds.txt",
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    (status_dir / "first.FA.output.analysis.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    fa_result_dir = base_dir / "4_make_library_analyze_fa" / "B_first_attempt_fa_result"
    fa_result_dir.mkdir(parents=True, exist_ok=True)
    (fa_result_dir / "thresholds.txt").write_text("lower=100\nupper=1000\n")
    (fa_result_dir / "reduced_fa_analysis_summary.txt").write_text("passed=280\nfailed=20\n")
    (fa_result_dir / "fa_smear_plate1.csv").write_text("sample_id,size_bp,conc\nL001,450,5.2\n")

    create_success_marker()
    print("Mock SIP step 9 (first_fa_analysis) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
