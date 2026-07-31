#!/usr/bin/env python3
"""
Extract AtomAmber and methodfile from a Gaussian ONIOM input file.

These files are used by the downstream Progdyn QM/MM dynamics setup.

Inputs:
    Gaussian ONIOM input file

Outputs:
    AtomAmber
    methodfile
"""

import sys


def is_charge_multiplicity_line(line: str) -> bool:
    """Return True if a line looks like an ONIOM charge/multiplicity line."""
    parts = line.split()

    if len(parts) != 6:
        return False

    try:
        [int(value) for value in parts]
    except ValueError:
        return False

    return True


if len(sys.argv) != 2:
    raise ValueError("Usage: python3 generate_aux_files_progdyn.py <oniom_input.com>")

file = sys.argv[1]

with open(file, "r") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if is_charge_multiplicity_line(line):
        flag_1 = i
        break
else:
    raise ValueError("Could not find ONIOM charge/multiplicity line.")

for i, line in enumerate(lines[flag_1 + 1:]):
    if "L" not in line and "H" not in line:
        flag_2 = i
        break
else:
    raise ValueError("Could not find end of AtomAmber atom block.")

with open("AtomAmber", "w") as f:
    for line in lines[flag_1 + 1:flag_1 + 1 + flag_2]:
        atom_label = line.split()[0]
        f.write(f"{atom_label}\n")

print("AtomAmber file generated.")

method_start = flag_1 + 1 + flag_2 + 1

for i, line in enumerate(lines[method_start:]):
    if "NonBon" in line:
        method_end = method_start + i
        break
else:
    raise ValueError("Could not find end of methodfile block marked by NonBon.")

with open("methodfile", "w") as f:
    for line in lines[method_start:method_end + 1]:
        f.write(line)

print("methodfile generated.")
