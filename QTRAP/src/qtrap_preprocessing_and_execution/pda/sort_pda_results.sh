#!/usr/bin/env bash
set -euo pipefail

# Collect PDA results from trajectory job directories and copy summarized
# decomposition files into the data/ directory.
#
# Inputs:
#   PDA job directories containing FINAL_DECOMP_MMPBSA.dat files
#
# Outputs:
#   shortened and renamed decomposition files in data/

mkdir -p ../data

for job_dir in */; do

        job_name="${job_dir%/}"

        if [[ "$job_name" != *"-oniom"* ]]; then
                continue
        fi

        # Extract trajectory and run information.

        structure_id="${job_name%-oniom*}"

        run_part="${job_name#*-oniom}"
        run_number="${run_part##*-}"

        cp mmpbsa_shortener.py "$job_dir"

        cd "$job_dir"

        if [[ -f "FINAL_DECOMP_MMPBSA.dat" ]]; then

                output_file="FINAL_DECOMP_MMPBSA-c-${structure_id}-r${run_number}.dat"

                python3 mmpbsa_shortener.py

                cp FINAL_DECOMP_MMPBSA-c.dat "../../data/$output_file"

        else
                echo "$job_name did not produce a results file."
        fi

        cd ..
done
