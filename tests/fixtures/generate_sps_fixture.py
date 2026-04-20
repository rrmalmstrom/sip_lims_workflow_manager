"""
SPS-CE workflow fixture generator for integration tests.

Creates a realistic on-disk project folder with fake but structurally correct
files at each step boundary. Used by tests/test_undo_system_integration_sps.py.

The fixture does NOT require real lab data. File sizes are irrelevant — the
snapshot system only cares about file paths and existence.

Real SPS-CE project structure (from boncat_peterson_lims2 reference):
  project_summary.db, sample_metadata.csv, individual_plates.csv  (root)
  1_make_barcode_labels/bartender_barcode_labels/
  1_make_barcode_labels/previously_process_label_input_files/custom_plates/
  1_make_barcode_labels/previously_process_label_input_files/standard_plates/
  2_sort_plates_and_amplify_genomes/A_sort_plate_layouts/
  2_sort_plates_and_amplify_genomes/B_WGA_results/
  3_make_library_analyze_fa/   (empty until step 4)
  4_pooling/                   (empty until step 9)
  archived_files/

Usage:
    from tests.fixtures.generate_sps_fixture import create_sps_fixture
    project_path, checkpoints = create_sps_fixture(tmp_path)
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Step definitions: what files each step produces
# These mirror the real SNAPSHOT_ITEMS in each SPS-CE script.
# ---------------------------------------------------------------------------

SPS_STEPS = [
    {
        "id": "initiate_project",
        "name": "Initiate Project and Make Sort Plate Labels",
        "script": "SPS_initiate_project_folder_and_make_sort_plate_labels.py",
        "allow_rerun": True,
        # Files this step creates/modifies (root-level + folder structure)
        "produces": [
            "project_summary.db",
            "sample_metadata.csv",
            "individual_plates.csv",
            "1_make_barcode_labels/bartender_barcode_labels/BARTENDER_sort_plate_labels.txt",
        ],
        # SNAPSHOT_ITEMS declared in the real script
        "snapshot_items": [
            "project_summary.db",
            "sample_metadata.csv",
            "individual_plates.csv",
        ],
        # Empty directories this step creates (for Scenario 13)
        "creates_empty_dirs": [
            "2_sort_plates_and_amplify_genomes",
            "3_make_library_analyze_fa",
            "4_pooling",
            "archived_files",
            "MISC",
        ],
    },
    {
        "id": "process_wga_results",
        "name": "Process WGA Results",
        "script": "SPS_process_WGA_results.py",
        "allow_rerun": False,
        "produces": [
            "2_sort_plates_and_amplify_genomes/B_WGA_results/summary_WGA_results.csv",
        ],
        "snapshot_items": [],
        "creates_empty_dirs": [],
    },
    {
        "id": "read_wga_and_make_spits",
        "name": "Read WGA Summary and Make SPITS",
        "script": "SPS_read_WGA_summary_and_make_SPITS.py",
        "allow_rerun": False,
        "produces": [
            "project_summary.db",
            "master_plate_data.csv",
            "2_sort_plates_and_amplify_genomes/B_WGA_results/SPITS_file.csv",
        ],
        "snapshot_items": [
            "project_summary.db",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "make_library_input_files",
        "name": "Make Library Creation Input Files",
        "script": "SPS_make_illumina_index_and_FA_files_NEW.py",
        "allow_rerun": True,
        "produces": [
            "project_summary.db",
            "master_plate_data.csv",
            "3_make_library_analyze_fa/A_first_attempt_make_lib/illumina_index_file.csv",
            "3_make_library_analyze_fa/A_first_attempt_make_lib/fa_transfer_file.csv",
            "3_make_library_analyze_fa/B_first_attempt_fa_result/thresholds.txt",
        ],
        "snapshot_items": [
            "project_summary.db",
            "master_plate_data.csv",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "first_fa_analysis",
        "name": "First FA Output Analysis",
        "script": "SPS_first_FA_output_analysis_NEW.py",
        "allow_rerun": True,
        "produces": [
            "3_make_library_analyze_fa/B_first_attempt_fa_result/reduced_fa_analysis_summary.txt",
            "3_make_library_analyze_fa/B_first_attempt_fa_result/fa_smear_plate1.csv",
        ],
        "snapshot_items": [],
        "creates_empty_dirs": [],
    },
    {
        "id": "second_attempt_decision",
        "name": "Second Attempt Decision",
        "script": "decision_second_attempt.py",
        "allow_rerun": False,
        "produces": [],
        "snapshot_items": [],
        "creates_empty_dirs": [],
    },
    {
        "id": "rework_first_attempt",
        "name": "Rework First Attempt",
        "script": "SPS_rework_first_attempt_NEW.py",
        "allow_rerun": True,
        "produces": [
            "project_summary.db",
            "master_plate_data.csv",
            "3_make_library_analyze_fa/C_second_attempt_make_lib/illumina_index_file_2nd.csv",
            "3_make_library_analyze_fa/D_second_attempt_fa_result/thresholds.txt",
        ],
        "snapshot_items": [
            "project_summary.db",
            "master_plate_data.csv",
        ],
        "creates_empty_dirs": [],
    },
    {
        "id": "second_fa_analysis",
        "name": "Second FA Output Analysis",
        "script": "SPS_second_FA_output_analysis_NEW.py",
        "allow_rerun": True,
        "produces": [
            "3_make_library_analyze_fa/D_second_attempt_fa_result/reduced_2nd_fa_analysis_summary.txt",
            "3_make_library_analyze_fa/D_second_attempt_fa_result/double_failed_libraries.txt",
        ],
        "snapshot_items": [],
        "creates_empty_dirs": [],
    },
    {
        "id": "conclude_fa_analysis",
        "name": "Conclude FA Analysis and Generate ESP Smear File",
        "script": "SPS_conclude_FA_analysis_generate_ESP_smear_file.py",
        "allow_rerun": True,
        "produces": [
            "project_summary.db",
            "master_plate_data.csv",
            "4_pooling/A_smear_file_for_ESP_upload/esp_smear_upload.csv",
        ],
        "snapshot_items": [
            "project_summary.db",
            "master_plate_data.csv",
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


def create_sps_fixture(
    base_dir: Path,
    steps_to_complete: int = 0,
) -> Tuple[Path, List[Dict]]:
    """
    Create an SPS-CE workflow project fixture on disk.

    Args:
        base_dir: Directory under which the project folder is created.
        steps_to_complete: Number of steps (0–9) to pre-complete in the fixture.
                           0 = fresh project (all steps pending).
                           N = first N steps marked completed with files on disk.

    Returns:
        (project_path, checkpoints) where:
          - project_path is the Path to the created project folder
          - checkpoints is a list of dicts, one per step boundary:
              checkpoints[0] = state before any step ran (initial)
              checkpoints[i] = state after step i completed (1-indexed)
    """
    project_path = base_dir / "sps_test_project"
    project_path.mkdir(parents=True, exist_ok=True)

    # --- Write workflow.yml ---
    workflow_content = _build_workflow_yml()
    (project_path / "workflow.yml").write_text(workflow_content)

    # --- Write initial workflow_state.json (all pending) ---
    initial_state = {step["id"]: "pending" for step in SPS_STEPS}
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

    for i, step in enumerate(SPS_STEPS):
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
    """Build the workflow.yml content from SPS_STEPS."""
    lines = ['workflow_name: "SPS-CE Library Creation Workflow"', "steps:"]
    for step in SPS_STEPS:
        lines.append(f'  - id: {step["id"]}')
        lines.append(f'    name: "{step["name"]}"')
        lines.append(f'    script: "{step["script"]}"')
        lines.append(f'    allow_rerun: {"true" if step["allow_rerun"] else "false"}')
        lines.append("")
    return "\n".join(lines)


def get_step_snapshot_items(step_id: str) -> List[str]:
    """Return the SNAPSHOT_ITEMS list for a given SPS-CE step ID."""
    for step in SPS_STEPS:
        if step["id"] == step_id:
            return step["snapshot_items"]
    raise ValueError(f"Unknown SPS-CE step ID: {step_id!r}")


def get_step_produces(step_id: str) -> List[str]:
    """Return the list of files a given SPS-CE step produces."""
    for step in SPS_STEPS:
        if step["id"] == step_id:
            return step["produces"]
    raise ValueError(f"Unknown SPS-CE step ID: {step_id!r}")
