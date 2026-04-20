#!/usr/bin/env python3
"""
FAILING mock script for SPS-CE Step 5: First FA Output Analysis.

Used by integration tests to simulate a script that:
  - Creates some output files (partial work)
  - Does NOT write a success marker
  - Exits with code 1

This triggers the automatic rollback path in handle_step_result().

IMPORTANT: SNAPSHOT_ITEMS must still be present — parse_snapshot_items_from_script()
reads this variable before the script runs.
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = []
# === END WORKFLOW SNAPSHOT ITEMS ===


def main():
    base_dir = Path(os.getcwd())

    # Partially create output files (simulating a script that crashes mid-run)
    fa_result_dir = base_dir / "3_make_library_analyze_fa" / "B_first_attempt_fa_result"
    fa_result_dir.mkdir(parents=True, exist_ok=True)
    (fa_result_dir / "fa_smear_partial.csv").write_text(
        "sample_id,size_bp\nS001,INCOMPLETE\n"
    )

    # Intentionally do NOT write a success marker
    # Intentionally exit with non-zero code
    print("Mock SPS step 5 FAILING — simulating script failure.")
    sys.exit(1)


if __name__ == "__main__":
    main()
