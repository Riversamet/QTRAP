#!/usr/bin/env python3
"""
Revise low positive frequencies in a Gaussian hpmodes output file.

Positive frequencies below the chosen threshold are raised to the threshold
value, and the corresponding force constants are scaled accordingly. This can
reduce excessive sampling along very soft, anharmonic modes during Progdyn
trajectory initialization.

The original file is backed up as <name>-unrevised.out.

Inputs:
    Gaussian hpmodes output file

Outputs:
    revised Gaussian output file
    unrevised backup output file
"""

import fileinput
import shutil
import sys
from pathlib import Path


if len(sys.argv) != 2:
    raise ValueError("Usage: python3 revise_frequencies.py <gaussian_output.out>")

frequency_file = Path(sys.argv[1])
backup_file = frequency_file.with_name(f"{frequency_file.stem}-unrevised.out")

threshold = 100.0

shutil.copy(frequency_file, backup_file)

frequency_line_index = -1
altered_indices = []
original_frequencies = []

for i, line in enumerate(fileinput.input(str(frequency_file), inplace=True)):
    if "Frequencies" in line:
        frequency_line_index = i
        altered_indices = []
        original_frequencies = []

        updated_line = line

        for j, value in enumerate(line.split()[2:]):
            frequency = float(value)

            if 0 < frequency < threshold:
                altered_indices.append(j)
                original_frequencies.append(frequency)

                updated_line = updated_line.replace(
                    f"{value:>10}",
                    f"{threshold:>10.4f}"
                )

        print(updated_line, end="")

    elif "Force constants" in line or "Frc consts" in line:
        if i == frequency_line_index + 2:
            updated_line = line

            for index, frequency in zip(altered_indices, original_frequencies):
                old_force_constant = line.split()[index + 3]
                old_force_constant_float = float(old_force_constant)

                new_force_constant = old_force_constant_float * (
                    threshold / frequency
                ) ** 2

                updated_line = updated_line.replace(
                    f"{old_force_constant_float:>10.4f}",
                    f"{new_force_constant:>10.4f}"
                )

            print(updated_line, end="")
        else:
            print(line, end="")

    else:
        print(line, end="")

print(f"Updated {frequency_file}; backup saved as {backup_file}")
