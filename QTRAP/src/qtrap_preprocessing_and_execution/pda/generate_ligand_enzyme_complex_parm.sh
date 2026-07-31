#!/usr/bin/env bash
set -euo pipefail

# Generate complex, receptor/enzyme, and ligand topology files for partial decomposition analysis.
#
# Inputs:
#   solvated Amber topology file
#   ligand mask
#   solvent and ion masks to remove
#
# Outputs:
#   complex.parm7
#   enzyme.parm7
#   ligand.parm7

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <input_topology> <ligand_mask> <solvent_ion_masks>"
    echo "Example: $0 frame_16000-cen.parm7 ':1' ':WAT :HOH :Na+ :Cl-'"
    exit 1
fi

input_topology="$1"
ligand_mask="$2"
strip_masks="$3"

module load amber

# Complex: remove solvent/ions.
cpptraj -p "$input_topology" <<EOF
$(for mask in $strip_masks; do echo "parmstrip $mask"; done)
parmwrite out complex.parm7
quit
EOF

# Enzyme/receptor: remove ligand.
cpptraj -p complex.parm7 <<EOF
parmstrip ${ligand_mask}
parmwrite out enzyme.parm7
quit
EOF

# Ligand: keep only ligand.
cpptraj -p complex.parm7 <<EOF
parmstrip !(${ligand_mask})
parmwrite out ligand.parm7
quit
EOF

echo "Generated complex.parm7, enzyme.parm7, and ligand.parm7."
