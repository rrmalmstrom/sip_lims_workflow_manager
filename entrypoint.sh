#!/bin/bash
set -e

# Activate the Conda environment
source activate sip-lims

# Execute the command passed to the script
exec "$@"