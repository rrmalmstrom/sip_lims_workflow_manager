"""
Capsule workflow fixture generator for integration tests.

Creates a realistic on-disk project folder with fake but structurally correct
files at each step boundary. Used by tests/test_undo_system_integration.py.

The fixture does NOT require real lab data. File sizes are irrelevant — the
snapshot system only cares about file paths and existence.

Usage:
    from tests.fixtures.generate_capsule_fixture import create_capsule_fixture
    project_path, checkpoints = create_capsule_fixture(tmp_path)
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# Step definitions: what files each step produces
# These mirror the real SNAPSHOT_ITEMS in each Capsule script.
# ---------------------------------------------------------------------------

CAPSULE_STEPS = [
    {
        "id": "init_project",
        "name": "1. Initiate Project / Make Sort Labels",
        "script": "initiate_project_folder_and_make_sort_plate_labels.py",
        "allow_rerun": True,
        # Files this step creates/modifies
        "produces": [
            "project_summary.db",
            "sample_metadata.csv",
            "individual_plates.csv",
            "1_make_barcode_labels/sort_plate_labels.csv",
            "1_make_barcode_labels/bartender_labels.csv",
        ],
        # SNAPSHOT_ITEMS declared in the real script
        "snapshot_items": [
            "project_summary.db",
            "sample_metadata.csv",
            "individual_plates.csv",
            "1_make_barcode_labels/",
        ],
    },
    {
        "id": "prep_library",
        "name": "2. Generate Lib Creation Files",
        "script": "generate_lib_creation_files.py",
        "allow_rerun": True,
        "produces": [
            "project_summary.db",
            "master_plate_data.csv",
            "individual_plates.csv",
            "2_library_creation/illumina_index_file.csv",
            "2_library_creation/fa_transfer_file.csv",
            "3_FA_analysis/thresholds.txt",
        ],
        "snapshot_items": [
            "project_summary.db",
            "master_plate_data.csv",
            "individual_plates.csv",
            "2_library_creation/",
            "3_FA_analysis/thresholds.txt",
        ],
    },
    {
        "id": "analyze_quality",
        "name": "3. Analyze FA data",
        "script": "capsule_fa_analysis.py",
        "allow_rerun": True,
        "produces": [
            "project_summary.db",
            "master_plate_data.csv",
            "individual_plates.csv",
            "3_FA_analysis/fa_summary.csv",
            "3_FA_analysis/fa_visualization.pdf",
            "3_FA_analysis/thresholds.txt",
        ],
        "snapshot_items": [
            "project_summary.db",
            "master_plate_data.csv",
            "individual_plates.csv",
            "3_FA_analysis/",
        ],
    },
    {
        "id": "select_plates",
        "name": "4. Create SPITS file",
        "script": "create_capsule_spits.py",
        "allow_rerun": False,
        "produces": [
            "project_summary.db",
            "master_plate_data.csv",
            "individual_plates.csv",
            "4_plate_selection_and_pooling/plate_selection.csv",
            "4_plate_selection_and_pooling/spits_file.csv",
        ],
        "snapshot_items": [
            "project_summary.db",
            "master_plate_data.csv",
            "individual_plates.csv",
            "4_plate_selection_and_pooling/",
        ],
    },
    {
        "id": "process_grid_barcodes",
        "name": "5. Process Grid Tables & Generate Barcodes",
        "script": "process_grid_tables_and_generate_barcodes.py",
        "allow_rerun": False,
        "produces": [
            "project_summary.db",
            "master_plate_data.csv",
            "individual_plates.csv",
            "4_plate_selection_and_pooling/grid_barcodes.csv",
            "4_plate_selection_and_pooling/bartender_grid_file.csv",
        ],
        "snapshot_items": [
            "project_summary.db",
            "master_plate_data.csv",
            "individual_plates.csv",
            "4_plate_selection_and_pooling/",
        ],
    },
    {
        "id": "verify_scanning_esp",
        "name": "6. Verify Scanning & Generate ESP Files",
        "script": "verify_scanning_and_generate_ESP_files.py",
        "allow_rerun": False,
        "produces": [
            "project_summary.db",
            "master_plate_data.csv",
            "individual_plates.csv",
            "4_plate_selection_and_pooling/C_smear_file_for_ESP_upload/esp_upload.csv",
            "4_plate_selection_and_pooling/C_smear_file_for_ESP_upload/smear_analysis.csv",
        ],
        "snapshot_items": [
            "project_summary.db",
            "master_plate_data.csv",
            "individual_plates.csv",
            "4_plate_selection_and_pooling/C_smear_file_for_ESP_upload/",
        ],
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


def create_capsule_fixture(
    base_dir: Path,
    steps_to_complete: int = 0,
) -> Tuple[Path, List[Dict]]:
    """
    Create a Capsule workflow project fixture on disk.

    Args:
        base_dir: Directory under which the project folder is created.
        steps_to_complete: Number of steps (0–6) to pre-complete in the fixture.
                           0 = fresh project (all steps pending).
                           N = first N steps marked completed with files on disk.

    Returns:
        (project_path, checkpoints) where:
          - project_path is the Path to the created project folder
          - checkpoints is a list of dicts, one per step boundary:
              checkpoints[0] = state before any step ran (initial)
              checkpoints[i] = state after step i completed (1-indexed)
    """
    project_path = base_dir / "capsule_test_project"
    project_path.mkdir(parents=True, exist_ok=True)

    # --- Write workflow.yml ---
    workflow_content = _build_workflow_yml()
    (project_path / "workflow.yml").write_text(workflow_content)

    # --- Write initial workflow_state.json (all pending) ---
    initial_state = {step["id"]: "pending" for step in CAPSULE_STEPS}
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

    for i, step in enumerate(CAPSULE_STEPS):
        if i >= steps_to_complete:
            break

        # Create the files this step produces
        for rel_path in step["produces"]:
            full_path = project_path / rel_path
            _write_fake_file(
                full_path,
                content=f"# {step['id']} output: {rel_path}\nstep={i+1}\n",
            )

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
    """Build the workflow.yml content from CAPSULE_STEPS."""
    lines = ['workflow_name: "Capsule Sorting"', "steps:"]
    for step in CAPSULE_STEPS:
        lines.append(f'  - id: {step["id"]}')
        lines.append(f'    name: "{step["name"]}"')
        lines.append(f'    script: "{step["script"]}"')
        lines.append(f'    allow_rerun: {"true" if step["allow_rerun"] else "false"}')
        lines.append("")
    return "\n".join(lines)


def get_step_snapshot_items(step_id: str) -> List[str]:
    """Return the SNAPSHOT_ITEMS list for a given Capsule step ID."""
    for step in CAPSULE_STEPS:
        if step["id"] == step_id:
            return step["snapshot_items"]
    raise ValueError(f"Unknown Capsule step ID: {step_id!r}")


def get_step_produces(step_id: str) -> List[str]:
    """Return the list of files a given Capsule step produces."""
    for step in CAPSULE_STEPS:
        if step["id"] == step_id:
            return step["produces"]
    raise ValueError(f"Unknown Capsule step ID: {step_id!r}")
