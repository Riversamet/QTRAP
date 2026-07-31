#!/usr/bin/env python3
"""
Create a rigid-residue ONIOM input file.

For low-layer atoms marked with layer 'L', this changes the Gaussian freeze
flag from 0 to -1, preventing those atoms from moving during optimization.

Inputs:
    Gaussian ONIOM .com file

Outputs:
    rigid-residue Gaussian ONIOM .com file
"""

import sys
from pathlib import Path


if len(sys.argv) != 2:
    raise ValueError("Usage: python3 rigid_low_level.py <input.com>")

input_file = Path(sys.argv[1])
output_file = input_file.with_name(f"{input_file.stem}-rigid.com")

with input_file.open("r") as input_handle, output_file.open("w") as output_handle:
    for line in input_handle:
        parts = line.split()

        if len(parts) > 5 and parts[5] == "L" and parts[1] == "0":
            line = line.replace("  0 ", " -1 ", 1)

        output_handle.write(line)

print(f"Rigid-residue file created: {output_file}")
