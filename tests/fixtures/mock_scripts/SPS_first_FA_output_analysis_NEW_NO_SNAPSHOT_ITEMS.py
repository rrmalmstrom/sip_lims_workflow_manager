#!/usr/bin/env python3
"""
NO_SNAPSHOT_ITEMS mock script for SPS-CE Step 5: First FA Output Analysis.

Used by Scenario 10 to verify that run_step() aborts with a clear error
when SNAPSHOT_ITEMS is missing from the script.

This script intentionally has NO SNAPSHOT_ITEMS variable.
parse_snapshot_items_from_script() will raise ValueError, causing run_step()
to abort before the script is ever executed.
"""

import sys
import os
from pathlib import Path


def main():
    # This code is never reached — run_step() aborts before launching the script
    print("This should never execute.")
    sys.exit(0)


if __name__ == "__main__":
    main()
