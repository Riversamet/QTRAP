#!/usr/bin/env bash
set -euo pipefail

# Generate final centered Amber topology, restart, and PDB files from stripped PDBs.
#
# Inputs:
#   residue name
#   tleap template
#   one or more stripped PDB files
#
# Outputs:
#   *-cen.parm7
#   *-cen.rst7
#   *-cen.pdb

if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <residue_name> <leap_template.in> <pdb1> [pdb2 ...]"
    echo "Example: $0 ITS leap.in frame_*-reorg-solv-stripped.pdb"
    exit 1
fi

residue_name="$1"
template="$2"
shift 2

module load amber

# Remove previous outputs from this step.
rm -f *-cen.parm7 *-cen.rst7 *-cen.pdb *-tleap.in

for pdb_file in "$@"; do
    base_name="${pdb_file%.pdb}"
    output_prefix="${base_name%-reorg-solv-stripped}-cen"
    leap_input="${base_name}-tleap.in"

    sed \
        -e "s|RESIDUE_NAME|${residue_name}|g" \
        -e "s|INPUT_PDB|${pdb_file}|g" \
        -e "s|OUTPUT_PREFIX|${output_prefix}|g" \
        "$template" > "$leap_input"

    tleap -f "$leap_input"

    rm -f "$leap_input"

    echo "Generated final Amber files for ${pdb_file}"
done
