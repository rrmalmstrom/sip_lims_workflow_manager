#!/usr/bin/env python3
"""
Mock script for SPS-CE Step 9: Conclude FA Analysis and Generate ESP Smear File.

SNAPSHOT_ITEMS: project_summary.db, master_plate_data.csv.
ESP smear files in 4_pooling/A_smear_file_for_ESP_upload/ are newly created —
manifest diff handles them.
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = [
    "project_summary.db",
    "master_plate_data.csv",
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    (status_dir / "SPS_conclude_FA_analysis_generate_ESP_smear_file.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "project_summary.db").write_text("mock sps db content - step 9 final\n")
    (base_dir / "master_plate_data.csv").write_text(
        "plate_id,lib_plate,index,final_pass\nP001,LP001,i701,yes\n"
    )

    esp_dir = base_dir / "4_pooling" / "A_smear_file_for_ESP_upload"
    esp_dir.mkdir(parents=True, exist_ok=True)
    (esp_dir / "esp_smear_upload.csv").write_text(
        "sample_id,size_bp,conc,pass\nS001,450,5.2,yes\n"
    )

    create_success_marker()
    print("Mock SPS step 9 (conclude_fa_analysis) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
