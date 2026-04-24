"""
READ-ONLY BENCHMARK — does not write, modify, or delete any files.

Benchmarks two restore-path directory-scanning strategies against a real
external-drive project folder to evaluate the DEV-013 optimisation for
sip_lims_workflow_manager.

The restore path in _restore_from_selective_snapshot() previously used:
  Walk 1: _scan_project_paths()  → os.scandir (fast, ~1.87 s) — files only
  Walk 2: project_path.rglob('*') → old rglob (~55-60 s)       — dirs only

DEV-013 replaces both walks with a single _scan_project() call that returns
(files, dirs) in one pass with early FA-archive/MISC pruning.

Usage:
    python utils/benchmark_restore.py

The external drive must be mounted at the path configured in TARGET_PATH below.
"""

import os
import sys
import time
import statistics
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration — update TARGET_PATH to point at a real project folder on the
# external drive that has FA archive / MISC subdirectories.
# ---------------------------------------------------------------------------

TARGET_PATH = Path(
    "/Volumes/gentech/Microscale_Application_STORAGE/SIP_STORAGE"
    "/511816_Chakraborty_second_batch"
)

RUNS_PER_STRATEGY = 3

# Mirror the constants from src/logic.py so the benchmark is self-contained.
_SCAN_EXCLUDE_NAMES = frozenset({
    '.snapshots',
    '.workflow_status',
    '.workflow_logs',
    'workflow.yml',
    '__pycache__',
    '.DS_Store',
})

PERMANENT_EXCLUSIONS = {
    "archived_files/FA_results_archive",
    "archived_files/first_lib_attempt_fa_results",
    "archived_files/second_lib_attempt_fa_results",
    "archived_files/third_lib_attempt_fa_results",
    "archived_files/capsule_fa_analysis_results",
    "MISC",
    "misc",
    "Misc",
}

_SCAN_EXCLUDE_PREFIXES = frozenset(PERMANENT_EXCLUSIONS)

# _MANIFEST_EXCLUDE_PATTERNS is the alias used in the old rglob filter
_MANIFEST_EXCLUDE_PATTERNS = _SCAN_EXCLUDE_NAMES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def print_banner():
    print()
    print("=" * 72)
    print("  READ-ONLY BENCHMARK — does not write, modify, or delete any files")
    print("  Benchmarks restore-path directory scanning (DEV-013)")
    print("=" * 72)
    print(f"  Target path : {TARGET_PATH}")
    print(f"  Runs each   : {RUNS_PER_STRATEGY}")
    print("=" * 72)
    print()


def check_target():
    if not TARGET_PATH.exists():
        print(f"ERROR: Target path does not exist or is not mounted:")
        print(f"       {TARGET_PATH}")
        print()
        print("Make sure the external drive 'gentech' is connected and mounted,")
        print("then re-run this script.")
        sys.exit(1)
    if not TARGET_PATH.is_dir():
        print(f"ERROR: Target path exists but is not a directory:")
        print(f"       {TARGET_PATH}")
        sys.exit(1)


def drop_caches_hint(strategy_name: str):
    print()
    print("  ┌─ NOTE ─────────────────────────────────────────────────────────┐")
    print(f"  │  Starting: {strategy_name:<54}│")
    print("  │  macOS does not expose a userspace cache-drop mechanism.       │")
    print("  │  Run 1 of each strategy may be faster than expected if the OS  │")
    print("  │  cached directory entries from a previous strategy's walk.     │")
    print("  │  Interpret run-1 times with that caveat in mind.               │")
    print("  └────────────────────────────────────────────────────────────────┘")
    print()


# ---------------------------------------------------------------------------
# Strategy implementations
# ---------------------------------------------------------------------------

def strategy_baseline_restore(root: Path):
    """
    OLD restore path (before DEV-013):
      Walk 1: _scan_project_paths() — os.scandir, files only (~1.87 s)
      Walk 2: project_path.rglob('*') — full rglob for dirs (~55-60 s)

    This simulates the two-walk pattern that _restore_from_selective_snapshot()
    used before the optimisation.
    """
    # Walk 1: os.scandir for files (already optimised by DEV-012)
    files: set = set()
    dirs_walk1: set = set()
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    if entry.name in _SCAN_EXCLUDE_NAMES:
                        continue
                    rel = str(Path(entry.path).relative_to(root))
                    if entry.is_dir(follow_symlinks=False):
                        if rel in _SCAN_EXCLUDE_PREFIXES:
                            continue
                        dirs_walk1.add(rel)
                        stack.append(Path(entry.path))
                    else:
                        files.add(rel)
        except PermissionError:
            pass

    # Walk 2: rglob for dirs (the OLD bottleneck — still uses rglob)
    current_dirs: set = set()
    for file_path in root.rglob('*'):
        if file_path.is_dir():
            rel = str(file_path.relative_to(root))
            if not any(part in _MANIFEST_EXCLUDE_PATTERNS for part in file_path.parts):
                current_dirs.add(rel)

    return len(files), len(current_dirs)


def strategy_optimised_restore(root: Path):
    """
    NEW restore path (DEV-013):
      Single _scan_project() call — returns (files, dirs) in one pass
      with early FA-archive/MISC pruning (~1.87 s total).

    This is what _restore_from_selective_snapshot() now does after the fix.
    """
    files: set = set()
    dirs: set = set()
    stack = [root]

    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    if entry.name in _SCAN_EXCLUDE_NAMES:
                        continue
                    rel = str(Path(entry.path).relative_to(root))
                    if entry.is_dir(follow_symlinks=False):
                        if rel in _SCAN_EXCLUDE_PREFIXES:
                            continue
                        dirs.add(rel)
                        stack.append(Path(entry.path))
                    else:
                        files.add(rel)
        except PermissionError:
            pass

    return len(files), len(dirs)


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

STRATEGIES = [
    (
        "Strategy 1: Baseline restore (scandir files + rglob dirs)",
        strategy_baseline_restore,
    ),
    (
        "Strategy 2: Optimised restore (single scandir, DEV-013)",
        strategy_optimised_restore,
    ),
]


def run_benchmarks(root: Path):
    results = []

    for strat_idx, (name, func) in enumerate(STRATEGIES, start=1):
        drop_caches_hint(name)
        run_times = []
        file_counts = []
        dir_counts = []

        for run_idx in range(1, RUNS_PER_STRATEGY + 1):
            print(f"  Running Strategy {strat_idx}, run {run_idx}/{RUNS_PER_STRATEGY}...", flush=True)
            t0 = time.perf_counter()
            n_files, n_dirs = func(root)
            t1 = time.perf_counter()
            elapsed = t1 - t0
            run_times.append(elapsed)
            file_counts.append(n_files)
            dir_counts.append(n_dirs)
            print(f"    → {elapsed:.2f}s  ({n_files} files, {n_dirs} dirs)", flush=True)

        results.append({
            "name": name,
            "times": run_times,
            "avg": statistics.mean(run_times),
            "files": file_counts[0],
            "dirs": dir_counts[0],
        })
        print()

    return results


# ---------------------------------------------------------------------------
# Results table
# ---------------------------------------------------------------------------

def print_results(results):
    baseline_avg = results[0]["avg"]

    print()
    print("=" * 72)
    print("  BENCHMARK RESULTS")
    print("=" * 72)

    col_name  = 46
    col_run   = 8
    col_avg   = 8
    col_files = 8
    col_dirs  = 8
    col_spdup = 8

    header = (
        f"{'Strategy':<{col_name}}"
        f"{'Run1':>{col_run}}"
        f"{'Run2':>{col_run}}"
        f"{'Run3':>{col_run}}"
        f"{'Avg':>{col_avg}}"
        f"{'Files':>{col_files}}"
        f"{'Dirs':>{col_dirs}}"
        f"{'Speedup':>{col_spdup}}"
    )
    print(header)
    print("-" * 72)

    for i, r in enumerate(results, start=1):
        t = r["times"]
        speedup = baseline_avg / r["avg"] if r["avg"] > 0 else float("inf")
        row = (
            f"{r['name']:<{col_name}}"
            f"{t[0]:>{col_run}.2f}"
            f"{t[1]:>{col_run}.2f}"
            f"{t[2]:>{col_run}.2f}"
            f"{r['avg']:>{col_avg}.2f}"
            f"{r['files']:>{col_files}}"
            f"{r['dirs']:>{col_dirs}}"
            f"{speedup:>{col_spdup}.2f}x"
        )
        print(row)

    print("=" * 72)
    print()


def print_summary(results):
    baseline = results[0]
    optimised = results[1]

    print("=" * 72)
    print("  SUMMARY — Restore path scan optimisation (DEV-013)")
    print("=" * 72)
    print()
    print(f"  Baseline (Strategy 1) average  : {baseline['avg']:.2f}s")
    print(f"  Optimised (Strategy 2) average : {optimised['avg']:.2f}s")
    speedup = baseline["avg"] / optimised["avg"] if optimised["avg"] > 0 else float("inf")
    print(f"  Speedup                        : {speedup:.2f}x")
    print()
    print("  What changed (DEV-013):")
    print("    Before: _scan_project_paths() [scandir, files only]")
    print("          + project_path.rglob('*') [rglob, dirs only]  ← bottleneck")
    print("    After:  _scan_project() [single scandir, files + dirs, early pruning]")
    print()
    print("  The rglob walk descended into FA archive and MISC subtrees,")
    print("  traversing hundreds of BMP/instrument files that are never")
    print("  included in manifests or snapshots. _scan_project() prunes")
    print("  those subtrees before entering them — matching the DEV-012")
    print("  optimisation applied to the snapshot-creation path.")
    print()
    if speedup >= 10:
        print(f"  ✅ DEV-013 confirmed: {speedup:.1f}x speedup on restore path.")
    elif speedup >= 2:
        print(f"  ✅ DEV-013 confirmed: {speedup:.1f}x speedup on restore path.")
    else:
        print("  ⚠️  Speedup lower than expected — OS caching may be masking the")
        print("     difference. Try running on a cold cache or with a larger dataset.")
    print()
    print("=" * 72)
    print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print_banner()
    check_target()

    print(f"  Target path confirmed: {TARGET_PATH}")
    print(f"  Starting benchmark ({len(STRATEGIES)} strategies × {RUNS_PER_STRATEGY} runs each)...")
    print()

    results = run_benchmarks(TARGET_PATH)
    print_results(results)
    print_summary(results)


if __name__ == "__main__":
    main()
