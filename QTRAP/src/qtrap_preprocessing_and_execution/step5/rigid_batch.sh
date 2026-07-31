#!/usr/bin/env bash
set -euo pipefail

# Batch wrapper for rigid_low_level.py.
# Generate rigid-residue ONIOM input files from Gaussian input files.
#
# Inputs:
#   Gaussian .com files
#
# Outputs:
#   *-rigid.com files

for file in *.com; do
    if [[ -f "$file" ]]; then
        python3 rigid_low_level.py "$file"
    fi
done
