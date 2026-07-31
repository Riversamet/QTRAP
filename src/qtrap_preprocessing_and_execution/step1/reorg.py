#!/usr/bin/env python3
"""
Reorder a PDB file so a selected residue appears first.

This is useful for QM/MM trajectory workflows where downstream scripts expect
the ligand, transition state, or reactive residue to be residue 1.

Inputs:
    PDB file
    residue number to move

Outputs:
    reordered PDB file
"""

import sys
import pytraj as pt

if len(sys.argv) != 3:
    raise ValueError(
        "Usage: python3 reorg.py <input.pdb> <residue_number>"
    )

input_pdb = sys.argv[1]
residue_number = sys.argv[2]
output_pdb = input_pdb.replace(".pdb", "-reorg.pdb")

traj = pt.load(str(input_pdb))

selected_residue = traj[f":{residue_number}"]
remaining_structure = traj[f"!:{residue_number}"]

reordered_structure = selected_residue + remaining_structure

pt.write_traj(str(output_pdb), reordered_structure, overwrite=True)

print(f"Wrote reordered PDB: {output_pdb}")