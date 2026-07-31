#!/usr/bin/env bash
set -euo pipefail

# Generate a base ONIOM Gaussian input using pdb2oniom_py.
#
# Inputs:
#   centered Amber file prefix
#   freeze threshold
#   corelist.txt
#   pdb2oniom directory
#
# Outputs:
#   *-oniom.com

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <input_prefix> <freeze_threshold> <corelist.txt> <pdb2oniom_dir>"
    echo "Example: $0 frame_15000-cen 5 corelist.txt ~/software/pdb2oniom"
    exit 1
fi

input_prefix="$1"
freeze_threshold="$2"
corelist="$3"
pdb2oniom_dir="$4"
work_dir="$(pwd)"

parm_file="${input_prefix}.parm7"
rst_file="${input_prefix}.rst7"
output_file="${work_dir}/${input_prefix}-oniom.com"

cp "$parm_file" "$pdb2oniom_dir/"
cp "$rst_file" "$pdb2oniom_dir/"
cp "$corelist" "$pdb2oniom_dir/corelist.txt"

cd "$pdb2oniom_dir"

# The pdb2oniom package should be installed within the virtual environment in this directory in order for pdb2oniom_py to run properly

source .venv/bin/activate
module load python

pdb2oniom_py \
    -p "$parm_file" \
    -r "$rst_file" \
    --resid corelist.txt \
    -n "$freeze_threshold"

mv newinput.gjf "$output_file"

cd "$work_dir"

echo "Generated ONIOM input: $output_file"
