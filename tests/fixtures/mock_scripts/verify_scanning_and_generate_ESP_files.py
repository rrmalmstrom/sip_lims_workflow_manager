#!/usr/bin/env python3
"""
Mock script for Step 6: Verify Scanning & Generate ESP Files.

Simulates what the real script does:
  - Creates/modifies SNAPSHOT_ITEMS files
  - Writes a success marker
  - Exits with code 0
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = [
    "project_summary.db",
    "master_plate_data.csv",
    "individual_plates.csv",
    "4_plate_selection_and_pooling/C_smear_file_for_ESP_upload/",
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    marker = status_dir / "verify_scanning_and_generate_ESP_files.success"
    marker.write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "project_summary.db").write_text("mock db content - step 6\n")
    (base_dir / "master_plate_data.csv").write_text("plate_id,esp_status\nP001,UPLOADED\n")
    (base_dir / "individual_plates.csv").write_text("plate_id,barcode,esp_status\nP001,BC001,UPLOADED\n")

    esp_dir = base_dir / "4_plate_selection_and_pooling" / "C_smear_file_for_ESP_upload"
    esp_dir.mkdir(parents=True, exist_ok=True)
    (esp_dir / "esp_upload.csv").write_text("sample_name,container_barcode\nSample1,CB001\n")
    (esp_dir / "smear_analysis.csv").write_text("sample_name,avg_size,result\nSample1,450,PASS\n")

    create_success_marker()
    print("Mock step 6 (verify_scanning_esp) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
