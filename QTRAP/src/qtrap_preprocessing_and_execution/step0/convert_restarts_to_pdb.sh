#!/usr/bin/env bash
set -euo pipefail

# Convert Amber restart files to PDB files using a shared topology.
#
# Inputs:
#   Amber topology file
#   one or more Amber restart files
#
# Outputs:
#   PDB files with names matching the input restart files

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <topology.prmtop> <restart1.rst> [restart2.rst ...]"
    exit 1
fi

topology="$1"
shift

module load amber

for rst_file in "$@"; do
    pdb_file="${rst_file%.rst}.pdb"
    ambpdb -p "$topology" -c "$rst_file" > "$pdb_file"
    echo "Wrote $pdb_file"
done
