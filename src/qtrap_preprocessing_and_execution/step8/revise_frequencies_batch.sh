#!/usr/bin/env bash
set -euo pipefail

# Batch wrapper for revise_frequencies.py.
# Revise low positive frequencies in Gaussian hpmodes output files.
#
# Inputs:
#   *-traj.out Gaussian hpmodes output files
#
# Outputs:
#   revised output files
#   unrevised backup files

shopt -s nullglob

for file in *-traj.out; do
    python3 revise_frequencies.py "$file"
done

echo "Frequency revision complete."
