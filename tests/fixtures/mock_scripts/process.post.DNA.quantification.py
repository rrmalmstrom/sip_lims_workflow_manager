#!/usr/bin/env python3
"""
Mock script for SIP Step 7: Process Post-DNA Quantification.

SNAPSHOT_ITEMS: lib_info.db, lib_info.csv.
New timestamped PDF plots in DNA_vs_Density_plots/ are newly created.
"""

import sys
import os
from pathlib import Path

# === WORKFLOW SNAPSHOT ITEMS ===
SNAPSHOT_ITEMS = [
    "lib_info.db",
    "lib_info.csv",
]
# === END WORKFLOW SNAPSHOT ITEMS ===


def create_success_marker():
    base_dir = Path(os.getcwd())
    status_dir = base_dir / ".workflow_status"
    status_dir.mkdir(exist_ok=True)
    (status_dir / "process.post.DNA.quantification.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    (base_dir / "lib_info.db").write_text("mock sip lib_info - step 7\n")
    (base_dir / "lib_info.csv").write_text(
        "lib_id,sample_id,fraction,dna_conc\nL001,SIP001,F1,12.5\n"
    )

    plots_dir = base_dir / "DNA_vs_Density_plots"
    plots_dir.mkdir(exist_ok=True)
    (plots_dir / "post_dna_quant_plot_run1.pdf").write_text("mock post-quant pdf\n")

    create_success_marker()
    print("Mock SIP step 7 (process_post_dna_quant) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
