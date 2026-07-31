#!/usr/bin/env bash
set -euo pipefail

# Collect and sort Progdyn trajectory files from completed dynamics directories.
#
# Inputs:
#   directory pattern
#   Progdyn n*/traj files
#
# Outputs:
#   trajectory .xyz files collected in trajs/

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <directory_pattern>"
    echo "Example: $0 frame"
    exit 1
fi

pattern="$1"
direction=$(basename "$(pwd)")
output_dir="../trajs"

mkdir -p "$output_dir"

shopt -s nullglob

for structure_dir in *"$pattern"*/; do
    structure_name="${structure_dir%/}"

    for traj_dir in "${structure_dir}"/n*/; do
        run_name=$(basename "$traj_dir")

        if [[ -f "${traj_dir}/traj" ]]; then
            output_file="${output_dir}/${direction}_${structure_name}-traj-${run_name}.xyz"
            cp "${traj_dir}/traj" "$output_file"
            echo "Copied ${traj_dir}/traj to ${output_file}"
        fi
    done
done
