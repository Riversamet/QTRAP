#!/usr/bin/env bash
set -euo pipefail

# Extract a transition-state/ligand residue from a reordered PDB file and
# generate GAFF-compatible Amber parameter files using antechamber and parmchk2.
#
# Inputs:
#   residue name
#   reordered PDB file
#   net charge
#   optional charge method
#
# Outputs:
#   residue PDB file
#   mol2 file
#   frcmod file

if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <residue_name> <input_pdb> <net_charge> [charge_method]"
    echo "Example: $0 ITS frame_15000-reorg.pdb -1 bcc"
    exit 1
fi

residue_name="$1"
input_pdb="$2"
net_charge="$3"
charge_method="${4:-bcc}"

output_pdb="${residue_name}.pdb"
output_mol2="${residue_name}.mol2"
output_frcmod="${residue_name}.frcmod"

module load amber

rm -f "$output_pdb" "$output_mol2" "$output_frcmod"

{
    grep -w "CRYST1" "$input_pdb" || true
    grep -w "$residue_name" "$input_pdb"
    grep -w "END" "$input_pdb" || true
} > "$output_pdb"

antechamber \
    -i "$output_pdb" \
    -fi pdb \
    -o "$output_mol2" \
    -fo mol2 \
    -c "$charge_method" \
    -nc "$net_charge" \
    -rn "$residue_name" \
    -at gaff \
    -s 2

parmchk2 \
    -i "$output_mol2" \
    -f mol2 \
    -o "$output_frcmod"

echo "Wrote $output_pdb"
echo "Wrote $output_mol2"
echo "Wrote $output_frcmod"
