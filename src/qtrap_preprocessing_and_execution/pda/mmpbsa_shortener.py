#!/usr/bin/env python3
"""
Extract ligand-residue decomposition rows from FINAL_DECOMP_MMPBSA.dat.

Inputs:
    FINAL_DECOMP_MMPBSA.dat

Outputs:
    FINAL_DECOMP_MMPBSA-c.dat
"""

import sys

with open("FINAL_DECOMP_MMPBSA.dat", "r") as f:
    lines = f.readlines()

lig_line = lines[11]

ligand_id = lig_line.split(",")[0].split()[0]

with open("FINAL_DECOMP_MMPBSA-c.dat", "w") as f:
    for line in lines[10:]:
        if line.split(",")[0].split()[0] == ligand_id:
            f.write(line)
        else:
            break

print("Successfully wrote shortened decomposition file.")
