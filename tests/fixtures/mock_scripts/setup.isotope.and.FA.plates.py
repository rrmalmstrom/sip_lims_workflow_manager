#!/usr/bin/env python3
"""
Mock script for SIP Step 1: Setup Plates & DB.

SNAPSHOT_ITEMS = [] — first script, creates everything from scratch.
All files are newly created; manifest diff handles cleanup on rollback.
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
    (status_dir / "setup.isotope.and.FA.plates.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    # Create root database files
    (base_dir / "project_database.db").write_text("mock sip project_database - step 1\n")
    (base_dir / "project_database.csv").write_text("sample_id,fraction\nSIP001,F1\n")

    # Create folder structure (empty dirs)
    for d in [
        "1_setup_isotope_qc_fa/input_files",
        "2_load_ultracentrifuge",
        "3_merge_density_vol_conc_files",
        "4_make_library_analyze_fa",
        "5_pooling",
        "archived_files",
        "DNA_vs_Density_plots",
    ]:
        (base_dir / d).mkdir(parents=True, exist_ok=True)

    # Create step 1 output files
    setup_dir = base_dir / "1_setup_isotope_qc_fa"
    (setup_dir / "isotope_transfer.csv").write_text("tube_id,isotope\nSIP001,13C\n")
    (setup_dir / "FA_input_plate1.csv").write_text("well,sample\nA1,SIP001\n")
    (setup_dir / "BARTENDER_isotope_and_FA_plate_barcodes.txt").write_text("mock bartender\n")
    (setup_dir / "input_files" / "sample_list.csv").write_text("sample_id\nSIP001\n")

    create_success_marker()
    print("Mock SIP step 1 (setup_plates) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
