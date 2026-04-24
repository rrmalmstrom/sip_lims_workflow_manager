"""
READ-ONLY BENCHMARK — does not write, modify, or delete any files.

Benchmarks four directory-scanning strategies against a real external-drive
project folder to evaluate performance optimizations for sip_lims_workflow_manager.

Usage:
    python utils/benchmark_scan.py
"""

import os
import sys
import time
import statistics
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

TARGET_PATH = Path(
    "/Volumes/gentech/Microscale_Application_STORAGE/SIP_STORAGE"
    "/511816_Chakraborty_second_batch"
)

RUNS_PER_STRATEGY = 3

# Exclusion set used by Strategies 3 and 4.
# These are folder *names* (path components) that should be pruned.
EXCLUSION_NAMES = {
    "FA_archive",
    "MISC",
    "workflow_snapshots",
    "__pycache__",
    ".git",
    "first_lib_attempt_fa_results",
    "second_lib_attempt_fa_results",
    "third_lib_attempt_fa_results",
}

# Manifest exclusion patterns mirroring _MANIFEST_EXCLUDE_PATTERNS in logic.py
# (not applied in the benchmark — we benchmark raw walk performance only)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def print_banner():
    print()
    print("=" * 72)
    print("  READ-ONLY BENCHMARK — does not write, modify, or delete any files")
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

def strategy1_baseline(root: Path):
    """
    Current approach (baseline): 3 separate rglob('*') calls.

    Simulates what the current code does:
      - _scan_project_paths()  → rglob #1  (scan_manifest)
      - _scan_project_dirs()   → rglob #2  (scan_manifest)
      - _scan_project_paths()  → rglob #3  (take_selective_snapshot)

    No exclusions are applied during the walk (files in excluded dirs are
    still traversed), exactly as the current code does.
    """
    # Walk 1: collect files (simulates _scan_project_paths for scan_manifest)
    files1 = set()
    for p in root.rglob("*"):
        if p.is_file():
            files1.add(str(p.relative_to(root)))

    # Walk 2: collect dirs (simulates _scan_project_dirs for scan_manifest)
    dirs1 = set()
    for p in root.rglob("*"):
        if p.is_dir():
            dirs1.add(str(p.relative_to(root)))

    # Walk 3: collect files again (simulates _scan_project_paths for take_selective_snapshot)
    files2 = set()
    for p in root.rglob("*"):
        if p.is_file():
            files2.add(str(p.relative_to(root)))

    return len(files1), len(dirs1)


def strategy2_single_rglob(root: Path):
    """
    Single rglob: 1 rglob('*') call, results reused for both files and dirs.

    Simulates merging all 3 walks into 1 (optimizations B+C).
    No exclusions applied.
    """
    files = set()
    dirs = set()
    for p in root.rglob("*"):
        rel = str(p.relative_to(root))
        if p.is_file():
            files.add(rel)
        elif p.is_dir():
            dirs.add(rel)

    return len(files), len(dirs)


def strategy3_single_rglob_with_exclusions(root: Path):
    """
    Single rglob + exclusions: 1 rglob('*') call, filter out entries whose
    path contains any excluded folder name as a path component.

    rglob still descends into excluded dirs (unavoidable with rglob), but
    results are filtered out after the fact.
    Simulates optimizations A+B+C.
    """
    files = set()
    dirs = set()
    for p in root.rglob("*"):
        # Check every component of the path for exclusion names
        if any(part in EXCLUSION_NAMES for part in p.parts):
            continue
        rel = str(p.relative_to(root))
        if p.is_file():
            files.add(rel)
        elif p.is_dir():
            dirs.add(rel)

    return len(files), len(dirs)


def strategy4_scandir_with_exclusions(root: Path):
    """
    os.scandir walk + exclusions: iterative os.scandir() walk that PRUNES
    excluded directories early — never descends into them at all.

    This avoids the I/O cost of traversing excluded subtrees entirely.
    Collects files and dirs in one pass.
    """
    files = set()
    dirs = set()

    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as it:
                for entry in it:
                    if entry.is_dir(follow_symlinks=False):
                        if entry.name in EXCLUSION_NAMES:
                            # Prune: do not recurse into this directory
                            continue
                        rel = str(Path(entry.path).relative_to(root))
                        dirs.add(rel)
                        stack.append(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        rel = str(Path(entry.path).relative_to(root))
                        files.add(rel)
        except PermissionError:
            # Skip directories we can't read
            pass

    return len(files), len(dirs)


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------

STRATEGIES = [
    (
        "Strategy 1: Baseline (3× rglob, no exclusions)",
        strategy1_baseline,
    ),
    (
        "Strategy 2: Single rglob (no exclusions)",
        strategy2_single_rglob,
    ),
    (
        "Strategy 3: Single rglob + exclusions (filter after walk)",
        strategy3_single_rglob_with_exclusions,
    ),
    (
        "Strategy 4: os.scandir + exclusions (prune before walk)",
        strategy4_scandir_with_exclusions,
    ),
]


def run_benchmarks(root: Path):
    results = []  # list of dicts

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
            "files": file_counts[0],   # should be consistent across runs
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

    # Header
    col_name  = 42
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
    best = min(results, key=lambda r: r["avg"])
    best_idx = results.index(best) + 1

    print("=" * 72)
    print("  SUMMARY")
    print("=" * 72)
    print()
    print(f"  Baseline (Strategy 1) average : {baseline['avg']:.2f}s")
    print(f"  Best strategy                 : Strategy {best_idx} — {best['name']}")
    print(f"  Best average time             : {best['avg']:.2f}s")
    speedup = baseline["avg"] / best["avg"] if best["avg"] > 0 else float("inf")
    print(f"  Speedup vs baseline           : {speedup:.2f}x")
    print()

    # Per-strategy commentary
    for i, r in enumerate(results, start=1):
        sp = baseline["avg"] / r["avg"] if r["avg"] > 0 else float("inf")
        tag = " ← FASTEST" if r is best else ""
        print(f"  Strategy {i}: avg={r['avg']:.2f}s  speedup={sp:.2f}x{tag}")

    print()
    print("  Interpretation:")
    print()

    s1_avg = results[0]["avg"]
    s2_avg = results[1]["avg"]
    s3_avg = results[2]["avg"]
    s4_avg = results[3]["avg"]

    # Walk-reduction gain (S1 → S2)
    walk_gain = s1_avg / s2_avg if s2_avg > 0 else float("inf")
    print(f"  • Reducing 3 rglob walks → 1 (S1→S2): {walk_gain:.2f}x speedup")
    print(f"    This is the pure benefit of eliminating redundant walks.")

    # Exclusion filter gain (S2 → S3)
    excl_gain = s2_avg / s3_avg if s3_avg > 0 else float("inf")
    print(f"  • Adding post-walk exclusion filter (S2→S3): {excl_gain:.2f}x speedup")
    print(f"    rglob still enters excluded dirs; only results are filtered.")

    # Pruning gain (S3 → S4)
    prune_gain = s3_avg / s4_avg if s4_avg > 0 else float("inf")
    print(f"  • Switching to scandir with early pruning (S3→S4): {prune_gain:.2f}x speedup")
    print(f"    scandir never enters excluded dirs — avoids I/O entirely.")

    # Overall gain
    overall = s1_avg / s4_avg if s4_avg > 0 else float("inf")
    print(f"  • Overall gain (S1 baseline → S4 scandir+prune): {overall:.2f}x speedup")
    print()

    if s4_avg < s3_avg < s2_avg < s1_avg:
        print("  ✅ Hypothesis confirmed: each optimization layer adds measurable")
        print("     benefit. os.scandir with early pruning is the clear winner.")
    elif s4_avg < s2_avg:
        print("  ✅ os.scandir with pruning outperforms rglob approaches.")
    else:
        print("  ⚠️  Results are mixed — OS caching may be masking differences.")
        print("     Consider running on a cold cache or with a larger dataset.")

    print()
    print("  NOTE: All times include OS-level caching effects. Run 1 of each")
    print("  strategy may benefit from cache warming by the previous strategy.")
    print("  The most reliable comparison is the average across all 3 runs.")
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
