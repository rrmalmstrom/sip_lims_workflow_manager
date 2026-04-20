#!/usr/bin/env python3
"""
Mock script for SIP Step 11: Analyze Library QC (2nd FA).

SNAPSHOT_ITEMS: 4_make_library_analyze_fa/D_second_attempt_fa_result/thresholds.txt.
FA archive goes to archived_files/FA_results_archive/second_lib_attempt_fa_results/
which is a PERMANENT_EXCLUSION — not listed here.
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = [
    "4_make_library_analyze_fa/D_second_attempt_fa_result/thresholds.txt",
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    (status_dir / "second.FA.output.analysis.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    fa2_dir = base_dir / "4_make_library_analyze_fa" / "D_second_attempt_fa_result"
    fa2_dir.mkdir(parents=True, exist_ok=True)
    (fa2_dir / "thresholds.txt").write_text("lower=100\nupper=1000\n")
    (fa2_dir / "reduced_2nd_fa_analysis_summary.txt").write_text("passed=260\nfailed=20\n")
    (fa2_dir / "double_failed_libraries.txt").write_text("L042\nL099\n")

    create_success_marker()
    print("Mock SIP step 11 (second_fa_analysis) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
