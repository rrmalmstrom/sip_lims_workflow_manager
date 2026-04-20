#!/usr/bin/env python3
"""
Mock script for SIP Step 3: Plot DNA/Density (QC).

SNAPSHOT_ITEMS = [] — purely additive, creates new timestamped plot files only.
The manifest diff handles deletion of newly-created plot files on rollback.
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
    (status_dir / "plot_DNAconc_vs_Density.success").write_text("success")


def main():
    base_dir = Path(os.getcwd())

    plots_dir = base_dir / "DNA_vs_Density_plots"
    plots_dir.mkdir(exist_ok=True)
    (plots_dir / "dna_vs_density_plot_run1.pdf").write_text("mock pdf plot\n")

    create_success_marker()
    print("Mock SIP step 3 (plot_dna_conc) completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()
