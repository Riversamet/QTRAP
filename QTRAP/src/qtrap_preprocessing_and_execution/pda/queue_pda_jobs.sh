#!/usr/bin/env bash
set -euo pipefail

# Set up and submit PDA jobs for all NetCDF trajectories in the current
# directory.
#
# This script assumes trajectory names contain "-oniom", which is removed
# to identify the corresponding modified-radii topology file.
#
# Inputs:
#   number of final frames to analyze
#   .nc trajectory files
#   matching modified-radii topology files
#   image.in, decomp.in, pda.sh, and helper scripts
#
# Outputs:
#   one job directory per trajectory
#   imaged trajectory files
#   submitted MMPBSA.py jobs

if [ "$#" -ne 1 ]; then
        echo "Usage: $0 <n_frames>"
        exit 1
fi

frames_to_analyze="$1"

module load amber

for file in *.nc; do
        trajectory_name="${file%.nc}"
        job_dir="$trajectory_name"

        mkdir -p "$job_dir"

        cp "$file" "$job_dir/"
        cp *.in "$job_dir/"

        # Determine the matching topology file from the QM/MM trajectory name.

        topology_prefix="${trajectory_name%-oniom*}"
        topology_name="${topology_prefix/forward_dyn_/}"
	topology_name="${topology_name/reverse_dyn_/}"
	topology_file="${topology_name}-bondi.parm7"

        cp "$topology_file" "$job_dir/"

        cp pda.sh "$job_dir/"
        cp read_frames.sh "$job_dir/"

        cp complex-bondi.parm7 "$job_dir/"
        cp enzyme-bondi.parm7 "$job_dir/"
        cp ligand-bondi.parm7 "$job_dir/"

        cd "$job_dir/"

        sed -e "s|xx|$topology_file|g" -i read_frames.sh
        sed -e "s|xy|$file|g" -i read_frames.sh

        cpptraj_output=$(bash read_frames.sh)

        total_frames=$(printf "%s\n" "$cpptraj_output" | sed -nE 's/.*reading ([0-9]+) of ([0-9]+).*/\2/p')

        first_frame=$((total_frames - frames_to_analyze))

        if [ "$first_frame" -lt 1 ]; then
                first_frame=1
        fi

        sed -e "s|xx|$file|g" -i image.in
        sed -e "s|xy|${trajectory_name}-i|g" -i image.in
        sed -e "s|xa|$topology_file|g" -i image.in
        sed -e "s|xz|$first_frame|g" -i image.in

        sed -e "s|xx|${trajectory_name}-i|g" -i pda.sh
        sed -e "s|xy|$topology_file|g" -i pda.sh

        cpptraj -i image.in
        qsub pda.sh

        cd ..
done
