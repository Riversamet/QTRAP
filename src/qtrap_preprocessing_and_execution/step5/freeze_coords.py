#!/usr/bin/env python3
"""
Insert Gaussian modredundant freeze constraints into an ONIOM input file.

The constraints are inserted immediately before the Amber parameter section.

Inputs:
    ONIOM Gaussian input file
    frozen-coordinate constraint file

Outputs:
    ONIOM Gaussian input file with frozen-coordinate constraints
"""

import sys
from pathlib import Path


if len(sys.argv) != 4:
    raise ValueError(
        "Usage: python3 freeze_coords.py <input.com> <output.com> <constraints.txt>"
    )

input_file = Path(sys.argv[1])
output_file = Path(sys.argv[2])
constraint_file = Path(sys.argv[3])

lines = input_file.read_text().splitlines(keepends=True)
constraints = constraint_file.read_text().splitlines(keepends=True)

for i, line in enumerate(lines):
    if "HrmStr1" in line:
        insertion_index = i
        break
else:
    raise ValueError("Could not find 'HrmStr1' in input file.")

with output_file.open("w") as f:
    f.writelines(lines[:insertion_index])
    f.writelines(constraints)
    f.write("\n")
    f.writelines(lines[insertion_index:])

print(f"Frozen-geometry file created: {output_file}")
