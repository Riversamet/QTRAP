#!/usr/bin/env bash
set -euo pipefail

# Strip distant solvent and ions from solvated PDB files using cpptraj.
#
# Inputs:
#   cpptraj strip template
#   residue range to retain nearby solvent around
#   solvent distance cutoff
#   one or more solvated PDB files
#
# Outputs:
#   stripped PDB files

if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <strip_template.in> <residue_range> <cutoff_angstrom> [pdb1 pdb2 ...]"
    echo "Example: $0 strip.in 1-149 5.0 frame_*-solv.pdb"
    exit 1
fi

template="$1"
residue_range="$2"
cutoff="$3"
shift 3

module load amber

for pdb_file in "$@"; do
    base_name="${pdb_file%.pdb}"
    output_pdb="${base_name}-stripped.pdb"
    cpptraj_input="${base_name}-strip.in"

    sed \
        -e "s|INPUT_PDB|${pdb_file}|g" \
        -e "s|OUTPUT_PDB|${output_pdb}|g" \
        -e "s|RESIDUE_RANGE|${residue_range}|g" \
        -e "s|CUTOFF|${cutoff}|g" \
        "$template" > "$cpptraj_input"

    cpptraj -i "$cpptraj_input"

    rm -f "$cpptraj_input"

    echo "Generated stripped PDB: ${output_pdb}"
done
