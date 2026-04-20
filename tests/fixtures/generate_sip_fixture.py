"""
SIP workflow fixture generator for integration tests.

Creates a realistic on-disk project folder with fake but structurally correct
files at each step boundary. Used by tests/test_undo_system_integration_sip.py.

The fixture does NOT require real lab data. File sizes are irrelevant — the
snapshot system only cares about file paths and existence.

Real SIP project structure (from 511816_Chakraborty_second_batch reference):
  project_database.db, project_database.csv  (root — steps 1–7)
  lib_info.db, lib_info.csv                  (root — steps 4–14)
  lib_info_submitted_to_clarity.db/csv       (root — steps 15–20)
  1_setup_isotope_qc_fa/                     (step 1 output)
  2_load_ultracentrifuge/                    (step 2 output)
  3_merge_density_vol_conc_files/            (steps 3–7 output)
  4_make_library_analyze_fa/                 (steps 8–14 output)
    A_first_attempt_make_lib/
    B_first_attempt_fa_result/
    C_second_attempt_make_lib/
    D_second_attempt_fa_result/
    E_third_attempt_make_lib/
    F_third_attempt_fa_result/
  5_pooling/                                 (steps 15–20 output)
    A_make_clarity_aliquot_upload_file/
    B_fill_clarity_lib_creation_file/
    C_assign_libs_to_pools/
    D_finish_pooling/
    E_pooling_and_rework/
    F_final_pooling_files/
  archived_files/                            (timestamped archives)
  DNA_vs_Density_plots/                      (step 3 output)

FA archive paths (PERMANENT_EXCLUSIONS):
  archived_files/FA_results_archive/first_lib_attempt_fa_results/
  archived_files/FA_results_archive/second_lib_attempt_fa_results/
  archived_files/FA_results_archive/third_lib_attempt_fa_results/

Usage:
    from tests.fixtures.generate_sip_fixture import create_sip_fixture
    project_path, checkpoints = create_sip_fixture(tmp_path)
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Step definitions: what files each step produces
# These mirror the real SNAPSHOT_ITEMS in each SIP script.
# ---------------------------------------------------------------------------

SIP_STEPS = [
    {
        "id": "setup_plates",
        "name": "1. Setup Plates & DB",
        "script": "setup.isotope.and.FA.plates.py",
        "allow_rerun": False,
        # SNAPSHOT_ITEMS = [] — first script, creates everything from scratch
        "produces": [
            "project_database.db",
            "project_database.csv",
            "1_setup_isotope_qc_fa/isotope_transfer.csv",
            "1_setup_isotope_qc_fa/FA_input_plate1.csv",
            "1_setup_isotope_qc_fa/BARTENDER_isotope_and_FA_plate_barcodes.txt",
            "1_setup_isotope_qc_fa/input_files/sample_list.csv",
        ],
        "snapshot_items": [],
        # Empty directories this step creates (for Scenario 13)
        "creates_empty_dirs": [
            "2_load_ultracentrifuge",
            "3_merge_density_vol_conc_files",
            "4_make_library_analyze_fa",
            "5_pooling",
            "archived_files",
            "DNA_vs_Density_plots",
        ],
    },
    {
        "id": "ultracentrifuge_transfer",
        "name": "2. Create Ultracentrifuge Tubes",
        "script": "ultracentrifuge.transfer.py",
        "allow_rerun": True,
        # SNAPSHOT_ITEMS: project_database.db, project_database.csv
        "produces": [
            "project_database.db",
            "project_database.csv",
            "2_load_ultracentrifuge/Hamilton_transfer_files/Ultracentrifuge_transfer_SIP001.csv",
            "2_load_ultracentrifuge/BARTENDER_files/BARTENDER_ultracentrifuge_tube_labels.txt",
        ],
        "snapshot_items": [
            "project_database.db",
            "project_database.csv",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "plot_dna_conc",
        "name": "3. Plot DNA/Density (QC)",
        "script": "plot_DNAconc_vs_Density.py",
        "allow_rerun": True,
        # SNAPSHOT_ITEMS = [] — only creates new plot files
        "produces": [
            "DNA_vs_Density_plots/dna_vs_density_plot_run1.pdf",
        ],
        "snapshot_items": [],
        "creates_empty_dirs": [],
    },
    {
        "id": "create_db_sequins",
        "name": "4. Create DB and Add Sequins",
        "script": "create.db.and.add.sequins.py",
        "allow_rerun": True,
        # SNAPSHOT_ITEMS: lib_info.db, lib_info.csv
        "produces": [
            "lib_info.db",
            "lib_info.csv",
            "3_merge_density_vol_conc_files/sequins/sequin_transfer_files_run1/sequin_SIP001.csv",
        ],
        "snapshot_items": [
            "lib_info.db",
            "lib_info.csv",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "select_fractions_cleanup",
        "name": "5. Select Fractions for Cleanup",
        "script": "select.fractions.for.clean.up.py",
        "allow_rerun": True,
        # SNAPSHOT_ITEMS: project_database.db, project_database.csv, lib_info.db, lib_info.csv
        "produces": [
            "project_database.db",
            "project_database.csv",
            "lib_info.db",
            "lib_info.csv",
            "3_merge_density_vol_conc_files/CsCl_cleanup_info/review_fractions_for_cleanup.csv",
        ],
        "snapshot_items": [
            "project_database.db",
            "project_database.csv",
            "lib_info.db",
            "lib_info.csv",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "generate_cscl_cleanup",
        "name": "6. Generate CsCl Cleanup Files",
        "script": "generate.CsCl.cleanup.files.py",
        "allow_rerun": True,
        # SNAPSHOT_ITEMS: lib_info.db, lib_info.csv
        "produces": [
            "lib_info.db",
            "lib_info.csv",
            "3_merge_density_vol_conc_files/CsCl_cleanup_info/Transfer_files_run1/hamilton_cleanup_transfer.csv",
        ],
        "snapshot_items": [
            "lib_info.db",
            "lib_info.csv",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "process_post_dna_quant",
        "name": "7. Process Post-DNA Quantification",
        "script": "process.post.DNA.quantification.py",
        "allow_rerun": True,
        # SNAPSHOT_ITEMS: lib_info.db, lib_info.csv
        "produces": [
            "lib_info.db",
            "lib_info.csv",
            "DNA_vs_Density_plots/post_dna_quant_plot_run1.pdf",
        ],
        "snapshot_items": [
            "lib_info.db",
            "lib_info.csv",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "make_library_condensed",
        "name": "8. Create Library Files (Condensed Plates)",
        "script": "make.library.creation.files.condensed.plates.py",
        "allow_rerun": False,
        # SNAPSHOT_ITEMS: project_database.db, project_database.csv, lib_info.db, lib_info.csv
        "produces": [
            "project_database.db",
            "project_database.csv",
            "lib_info.db",
            "lib_info.csv",
            "4_make_library_analyze_fa/A_first_attempt_make_lib/echo_transfer_file.csv",
            "4_make_library_analyze_fa/A_first_attempt_make_lib/illumina_index_file.csv",
            "4_make_library_analyze_fa/B_first_attempt_fa_result/thresholds.txt",
        ],
        "snapshot_items": [
            "project_database.db",
            "project_database.csv",
            "lib_info.db",
            "lib_info.csv",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "first_fa_analysis",
        "name": "9. Analyze Library QC (1st)",
        "script": "first.FA.output.analysis.py",
        "allow_rerun": False,
        # SNAPSHOT_ITEMS: 4_make_library_analyze_fa/B_first_attempt_fa_result/thresholds.txt
        "produces": [
            "4_make_library_analyze_fa/B_first_attempt_fa_result/thresholds.txt",
            "4_make_library_analyze_fa/B_first_attempt_fa_result/reduced_fa_analysis_summary.txt",
            "4_make_library_analyze_fa/B_first_attempt_fa_result/fa_smear_plate1.csv",
        ],
        "snapshot_items": [
            "4_make_library_analyze_fa/B_first_attempt_fa_result/thresholds.txt",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "rework_first_attempt",
        "name": "10. Second Attempt Library Creation",
        "script": "rework.first.attempt.py",
        "allow_rerun": False,
        # SNAPSHOT_ITEMS: project_database.db, project_database.csv, lib_info.db, lib_info.csv
        "produces": [
            "project_database.db",
            "project_database.csv",
            "lib_info.db",
            "lib_info.csv",
            "4_make_library_analyze_fa/C_second_attempt_make_lib/echo_transfer_file_2nd.csv",
            "4_make_library_analyze_fa/D_second_attempt_fa_result/thresholds.txt",
        ],
        "snapshot_items": [
            "project_database.db",
            "project_database.csv",
            "lib_info.db",
            "lib_info.csv",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "second_fa_analysis",
        "name": "11. Analyze Library QC (2nd)",
        "script": "second.FA.output.analysis.py",
        "allow_rerun": False,
        # SNAPSHOT_ITEMS: 4_make_library_analyze_fa/D_second_attempt_fa_result/thresholds.txt
        "produces": [
            "4_make_library_analyze_fa/D_second_attempt_fa_result/thresholds.txt",
            "4_make_library_analyze_fa/D_second_attempt_fa_result/reduced_2nd_fa_analysis_summary.txt",
            "4_make_library_analyze_fa/D_second_attempt_fa_result/double_failed_libraries.txt",
        ],
        "snapshot_items": [
            "4_make_library_analyze_fa/D_second_attempt_fa_result/thresholds.txt",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "third_attempt_decision",
        "name": "Decision: Third Library Creation Attempt",
        "script": "decision_third_attempt.py",
        "allow_rerun": False,
        # SNAPSHOT_ITEMS = [] — decision script only
        "produces": [],
        "snapshot_items": [],
        "creates_empty_dirs": [],
    },
    {
        "id": "rework_second_attempt",
        "name": "12. Third Attempt Library Creation",
        "script": "emergency.third.attempt.rework.py",
        "allow_rerun": False,
        # SNAPSHOT_ITEMS: project_database.db, project_database.csv, lib_info.db, lib_info.csv
        "produces": [
            "project_database.db",
            "project_database.csv",
            "lib_info.db",
            "lib_info.csv",
            "4_make_library_analyze_fa/E_third_attempt_make_lib/echo_transfer_file_3rd.csv",
            "4_make_library_analyze_fa/F_third_attempt_fa_result/thresholds.txt",
        ],
        "snapshot_items": [
            "project_database.db",
            "project_database.csv",
            "lib_info.db",
            "lib_info.csv",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "third_fa_analysis",
        "name": "13. Analyze Library QC (3rd)",
        "script": "emergency.third.FA.output.analysis.py",
        "allow_rerun": False,
        # SNAPSHOT_ITEMS: 4_make_library_analyze_fa/F_third_attempt_fa_result/thresholds.txt
        "produces": [
            "4_make_library_analyze_fa/F_third_attempt_fa_result/thresholds.txt",
            "4_make_library_analyze_fa/F_third_attempt_fa_result/reduced_3rd_fa_analysis_summary.txt",
            "4_make_library_analyze_fa/F_third_attempt_fa_result/triple_failed_libraries.txt",
        ],
        "snapshot_items": [
            "4_make_library_analyze_fa/F_third_attempt_fa_result/thresholds.txt",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "conclude_fa_analysis",
        "name": "14. Conclude FA analysis",
        "script": "conclude.all.fa.analysis.py",
        "allow_rerun": False,
        # SNAPSHOT_ITEMS: lib_info.db, lib_info.csv
        "produces": [
            "lib_info.db",
            "lib_info.csv",
            "5_pooling/A_make_clarity_aliquot_upload_file/final_lib_summary.csv",
        ],
        "snapshot_items": [
            "lib_info.db",
            "lib_info.csv",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "make_clarity_summary",
        "name": "15. Make Clarity Summary",
        "script": "make.clarity.summary.py",
        "allow_rerun": False,
        # SNAPSHOT_ITEMS: lib_info.db, lib_info.csv,
        #   5_pooling/A_make_clarity_aliquot_upload_file/final_lib_summary.csv
        "produces": [
            "lib_info.db",
            "lib_info.csv",
            "5_pooling/A_make_clarity_aliquot_upload_file/final_lib_summary.csv",
            "5_pooling/A_make_clarity_aliquot_upload_file/clarity_summary.xlsx",
            "lib_info_submitted_to_clarity.db",
            "lib_info_submitted_to_clarity.csv",
        ],
        "snapshot_items": [
            "lib_info.db",
            "lib_info.csv",
            "5_pooling/A_make_clarity_aliquot_upload_file/final_lib_summary.csv",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "generate_pool_tool",
        "name": "16. Generate Pool Assignment Tool",
        "script": "generate_pool_assignment_tool.py",
        "allow_rerun": False,
        # SNAPSHOT_ITEMS = [] — only creates new files
        "produces": [
            "5_pooling/C_assign_libs_to_pools/assign_pool_number_sheet.xlsx",
        ],
        "snapshot_items": [],
        "creates_empty_dirs": [],
    },
    {
        "id": "run_pooling_preparation",
        "name": "17. Prepare Pools",
        "script": "run.pooling.preparation.py",
        "allow_rerun": False,
        # SNAPSHOT_ITEMS: lib_info_submitted_to_clarity.db, lib_info_submitted_to_clarity.csv,
        #   5_pooling/C_assign_libs_to_pools/assign_pool_number_sheet.xlsx
        "produces": [
            "lib_info_submitted_to_clarity.db",
            "lib_info_submitted_to_clarity.csv",
            "5_pooling/C_assign_libs_to_pools/assign_pool_number_sheet.xlsx",
            "5_pooling/pool_summary.csv",
            "5_pooling/E_pooling_and_rework/Attempt_1/hamilton_transfer.csv",
        ],
        "snapshot_items": [
            "lib_info_submitted_to_clarity.db",
            "lib_info_submitted_to_clarity.csv",
            "5_pooling/C_assign_libs_to_pools/assign_pool_number_sheet.xlsx",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "pool_fa12_analysis",
        "name": "18. Analyze Pool QC Results",
        "script": "pool.FA12.analysis.py",
        "allow_rerun": True,
        # SNAPSHOT_ITEMS: 5_pooling/pool_summary.csv
        "produces": [
            "5_pooling/pool_summary.csv",
            "5_pooling/E_pooling_and_rework/Attempt_1/fa_smear_pool1.csv",
        ],
        "snapshot_items": [
            "5_pooling/pool_summary.csv",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "rework_pooling",
        "name": "19. Rework Pools & Finalize",
        "script": "rework.pooling.steps.py",
        "allow_rerun": True,
        # SNAPSHOT_ITEMS: 5_pooling/pool_summary.csv,
        #   lib_info_submitted_to_clarity.db, lib_info_submitted_to_clarity.csv
        "produces": [
            "5_pooling/pool_summary.csv",
            "lib_info_submitted_to_clarity.db",
            "lib_info_submitted_to_clarity.csv",
            "5_pooling/E_pooling_and_rework/Attempt_2/hamilton_transfer.csv",
        ],
        "snapshot_items": [
            "5_pooling/pool_summary.csv",
            "lib_info_submitted_to_clarity.db",
            "lib_info_submitted_to_clarity.csv",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "transfer_pools",
        "name": "20. Transfer Pools to Final Tubes",
        "script": "transfer.pools.to.final.tubes.py",
        "allow_rerun": False,
        # SNAPSHOT_ITEMS: lib_info_submitted_to_clarity.db, lib_info_submitted_to_clarity.csv
        "produces": [
            "lib_info_submitted_to_clarity.db",
            "lib_info_submitted_to_clarity.csv",
            "5_pooling/F_final_pooling_files/hamilton_final_transfer.csv",
        ],
        "snapshot_items": [
            "lib_info_submitted_to_clarity.db",
            "lib_info_submitted_to_clarity.csv",
        ],
        "creates_empty_dirs": [],
    },
]


def _write_fake_file(path: Path, content: str = "") -> None:
    """Create a file with minimal fake content."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content or f"# fake content for {path.name}\n")


def _snapshot_project(project_path: Path) -> Dict[str, str]:
    """
    Capture the current file system state as a dict of {relative_path: content}.
    Used to create reference checkpoints for assertions.
    Excludes .snapshots/, .workflow_status/, .workflow_logs/, workflow.yml,
    workflow_state.json, and __pycache__.
    """
    exclude = {".snapshots", ".workflow_status", ".workflow_logs", "__pycache__"}
    snapshot = {}
    for p in sorted(project_path.rglob("*")):
        if p.is_file():
            parts = p.relative_to(project_path).parts
            if not any(part in exclude for part in parts):
                rel = str(p.relative_to(project_path))
                try:
                    snapshot[rel] = p.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    snapshot[rel] = "<binary>"
    return snapshot


def create_sip_fixture(
    base_dir: Path,
    steps_to_complete: int = 0,
) -> Tuple[Path, List[Dict]]:
    """
    Create a SIP workflow project fixture on disk.

    Args:
        base_dir: Directory under which the project folder is created.
        steps_to_complete: Number of steps (0–20) to pre-complete in the fixture.
                           0 = fresh project (all steps pending).
                           N = first N steps marked completed with files on disk.

    Returns:
        (project_path, checkpoints) where:
          - project_path is the Path to the created project folder
          - checkpoints is a list of dicts, one per step boundary:
              checkpoints[0] = state before any step ran (initial)
              checkpoints[i] = state after step i completed (1-indexed)
    """
    project_path = base_dir / "sip_test_project"
    project_path.mkdir(parents=True, exist_ok=True)

    # --- Write workflow.yml ---
    workflow_content = _build_workflow_yml()
    (project_path / "workflow.yml").write_text(workflow_content)

    # --- Write initial workflow_state.json (all pending) ---
    initial_state = {step["id"]: "pending" for step in SIP_STEPS}
    state_file = project_path / "workflow_state.json"
    state_file.write_text(json.dumps(initial_state, indent=2))

    # --- Create required directories ---
    (project_path / ".workflow_status").mkdir(exist_ok=True)
    (project_path / ".snapshots").mkdir(exist_ok=True)

    # --- Checkpoint 0: state before any step ran ---
    checkpoints = [_snapshot_project(project_path)]

    # --- Pre-complete requested steps ---
    state = dict(initial_state)
    completion_order = []

    for i, step in enumerate(SIP_STEPS):
        if i >= steps_to_complete:
            break

        # Create the files this step produces
        for rel_path in step["produces"]:
            full_path = project_path / rel_path
            _write_fake_file(
                full_path,
                content=f"# {step['id']} output: {rel_path}\nstep={i+1}\n",
            )

        # Create empty directories this step creates (folder structure)
        for rel_dir in step.get("creates_empty_dirs", []):
            (project_path / rel_dir).mkdir(parents=True, exist_ok=True)

        # Mark step completed in state
        state[step["id"]] = "completed"
        completion_order.append(step["id"])
        state["_completion_order"] = completion_order
        state_file.write_text(json.dumps(state, indent=2))

        # Create success marker
        script_stem = Path(step["script"]).stem
        (project_path / ".workflow_status" / f"{script_stem}.success").write_text(
            "success"
        )

        # Checkpoint after this step
        checkpoints.append(_snapshot_project(project_path))

    return project_path, checkpoints


def _build_workflow_yml() -> str:
    """Build the workflow.yml content from SIP_STEPS."""
    lines = ['workflow_name: "SIP Fractionation and Library Prep"', "steps:"]
    for step in SIP_STEPS:
        lines.append(f'  - id: {step["id"]}')
        lines.append(f'    name: "{step["name"]}"')
        lines.append(f'    script: "{step["script"]}"')
        lines.append(f'    allow_rerun: {"true" if step["allow_rerun"] else "false"}')
        lines.append("")
    return "\n".join(lines)


def get_step_snapshot_items(step_id: str) -> List[str]:
    """Return the SNAPSHOT_ITEMS list for a given SIP step ID."""
    for step in SIP_STEPS:
        if step["id"] == step_id:
            return step["snapshot_items"]
    raise ValueError(f"Unknown SIP step ID: {step_id!r}")


def get_step_produces(step_id: str) -> List[str]:
    """Return the list of files a given SIP step produces."""
    for step in SIP_STEPS:
        if step["id"] == step_id:
            return step["produces"]
    raise ValueError(f"Unknown SIP step ID: {step_id!r}")
