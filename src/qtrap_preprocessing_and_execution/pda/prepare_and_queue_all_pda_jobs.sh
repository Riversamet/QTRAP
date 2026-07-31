#!/usr/bin/env bash
set -euo pipefail

# Run the full QM/MM partial decomposition analysis workflow for forward and reverse trajectories.
# This script stages trajectory files, converts xyz trajectories to NetCDF,
# applies modified Bondi radii, and submits partial decomposition analysis (PDA) jobs.
#
# Inputs:
#   forward and reverse trajectory files from the QM/MM dynamics step
#   PDA input files
#   topology files
#   conda environment name containing MDTraj package
#
# Outputs:
#   forward and reverse PDA working directories
#   submitted PDA jobs

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <frames_to_analyze> <mdtraj_env>"
    exit 1
fi

frames_to_analyze="$1"

# Transfer trajectory files and shared PDA files into the forward and reverse
# analysis directories.

bash get_traj_files.sh

# Convert xyz trajectories, apply modified radii, and queue PDA jobs for each
# trajectory direction.

module load conda
conda activate amberpy

for direction in forward reverse; do

    cd "$direction"

    python xyz_to_nc_converter.py

    bash bondi_radii.sh

    bash queue_pda_jobs.sh "$frames_to_analyze"

    cd ..
done
