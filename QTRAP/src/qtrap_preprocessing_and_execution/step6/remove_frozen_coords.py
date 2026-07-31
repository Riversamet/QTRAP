#!/usr/bin/env python3
"""
Remove Gaussian modredundant freeze constraints from an ONIOM input file.

This is used after a frozen-coordinate TS optimization succeeds, so the next
optimization can continue from the updated structure without the frozen
modredundant coordinate block.

Inputs:
    frozen-coordinate ONIOM .com file
    frozen-coordinate constraint file

Outputs:
    unfrozen ONIOM .com file
"""

import sys
from pathlib import Path


if len(sys.argv) != 4:
    raise ValueError(
        "Usage: python3 remove_frozen_coords.py <input.com> <output.com> <constraints.txt>"
    )

input_file = Path(sys.argv[1])
output_file = Path(sys.argv[2])
constraint_file = Path(sys.argv[3])

lines = input_file.read_text().splitlines(keepends=True)
constraint_lines = constraint_file.read_text().splitlines(keepends=True)

# Also remove the blank line immediately after the constraint block.
last_constraint = constraint_lines[-1]
blank_line_after_constraints = None

for i, line in enumerate(lines):
    if line == last_constraint:
        blank_line_after_constraints = i + 1
        break

with output_file.open("w") as f:
    for i, line in enumerate(lines):
        if line in constraint_lines:
            continue

        if blank_line_after_constraints is not None and i == blank_line_after_constraints:
            continue

        f.write(line)

print(f"Unfrozen ONIOM input written to {output_file}")
