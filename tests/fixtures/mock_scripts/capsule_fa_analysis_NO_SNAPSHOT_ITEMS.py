#!/usr/bin/env python3
"""
Mock script WITHOUT SNAPSHOT_ITEMS — used to test that run_step() aborts
with a ValueError when SNAPSHOT_ITEMS is missing from the script.

This script intentionally omits the SNAPSHOT_ITEMS variable.
parse_snapshot_items_from_script() will raise ValueError when it reads this file,
causing run_step() to abort before the script is ever executed.

The test verifies:
  - No ZIP or manifest is created in .snapshots/
  - The project folder is unchanged
  - The step state remains "pending"
"""

import sys
import os
from pathlib import Path

# NOTE: SNAPSHOT_ITEMS is intentionally absent from this file.


def main():
    # This code should NEVER be reached in tests — run_step() aborts before
    # launching the script because SNAPSHOT_ITEMS is missing.
    print("ERROR: This script should never run — SNAPSHOT_ITEMS is missing.")
    sys.exit(1)


if __name__ == "__main__":
    main()
