#!/usr/bin/env bash
set -euo pipefail

# Build solvated Amber structures from reordered PDB files using tleap.
#
# Inputs:
#   residue name
#   tleap template
#   one or more reordered PDB files
#
# Outputs:
#   solvated PDB, topology, and coordinate files

if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <residue_name> <leap_template.in> <pdb1> [pdb2 ...]"
    echo "Example: $0 ITS leap.in frame_*-reorg.pdb"
    exit 1
fi

residue_name="$1"
template="$2"
shift 2

module load amber

# Remove existing tleap outputs
rm -f *-solv.prmtop *-solv.inpcrd *-solv.pdb *-tleap.in

for pdb_file in "$@"; do
    base_name="${pdb_file%.pdb}"
    output_prefix="${base_name}-solv"
    leap_input="${base_name}-tleap.in"

    sed \
        -e "s/LIG/${residue_name}/g" \
        -e "s|INPUT_PDB|${pdb_file}|g" \
        -e "s|OUTPUT_PREFIX|${output_prefix}|g" \
        "$template" > "$leap_input"

    tleap -f "$leap_input"
    
    rm -f "$leap_input" 

    echo "Generated solvated Amber files for ${pdb_file}"
done
