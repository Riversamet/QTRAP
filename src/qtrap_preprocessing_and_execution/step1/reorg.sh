#!/usr/bin/env bash
set -euo pipefail

# Batch wrapper for reorg.py.
# Reorder one or more PDB files so a selected residue appears first.
#
# Inputs:
#   residue number
#   environment containing pytraj package
#   one or more PDB files
#
# Outputs:
#   reordered PDB files

if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <residue_number> <pytraj_env> <pdb1> [pdb2 ...]"
    echo "Example: $0 149 amberpy frame_*.pdb"
    exit 1
fi

residue_number="$1"
pytraj_env="$2"
shift 2

module purge
module load conda
conda activate "$pytraj_env"

for pdb_file in "$@"; do
    python3 reorg.py "$pdb_file" "$residue_number"
done
