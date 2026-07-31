#!/usr/bin/env bash
set -euo pipefail

# Convert Amber topology radii to Bondi radii for GBSA/MMPBSA calculations.
#
# Inputs:
#   Amber .parm7 topology files
#
# Outputs:
#   *-bondi.parm7 topology files

module load amber

for file in *.parm7; do
    newname="${file%.parm7}"
    fname="${newname}-bondi.parm7"

    parmed -p "$file" <<EOF
changeRadii bondi
outparm $fname
quit
EOF
done
