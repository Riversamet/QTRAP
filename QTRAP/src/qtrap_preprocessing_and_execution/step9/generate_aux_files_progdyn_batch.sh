#!/usr/bin/env bash
set -euo pipefail

# Batch wrapper for generate_aux_files_progdyn.py
#
# Prepare Progdyn auxiliary files for each revised hpmodes output.
#
# Inputs:
#   *-traj.out Gaussian output files
#   matching *-traj.com files from the previous step
#
# Outputs:
#   per-structure directories containing Progdyn auxiliary files
#   copied setup directories in the QM/MM dynamics step

qmmm_dir="../step10"

shopt -s nullglob

for file in *-traj.out; do
    newname="${file%-traj.out}"

    mkdir -p "$newname"

    cp "../step7/${newname}-traj.com" "$newname/"
    cp "$file" "$newname/"
    cp generate_aux_files_progdyn.py "$newname/"

    (
        cd "$newname"
        python3 generate_aux_files_progdyn.py "${newname}-traj.com"
        rm -f generate_aux_files_progdyn.py
    )

    cp -r "$newname" "$qmmm_dir/"

    echo "Prepared Progdyn files for $newname"
done
