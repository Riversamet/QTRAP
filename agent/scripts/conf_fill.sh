#!/usr/bin/env bash
set -euo pipefail

# Fill in progdyn.conf's per-run placeholders. Method, overall charge,
# and highlevel atom count are parsed from one representative .com file
# already in the target directory; everything else is passed in
# directly as arguments.
#
# Not part of src/ -- referenced directly from agent/scripts/, not
# copied into the run's own directory.
#
# Inputs:
#   directory pattern
#   basis set
#   overall multiplicity
#   ligand charge
#   ligand multiplicity
#   title
#   temperature
#   thermostat multiplier
#   empirical dispersion
#   radius multiplier
#   etolerance
#   damping
#
# Outputs:
#   progdyn.conf in the current directory, with its placeholder fields
#   filled in

if [ "$#" -lt 12 ]; then
    echo "Usage: $0 <directory_pattern> <basis> <overall_multiplicity> <ligand charge> <ligand_mult> <title> <temp> <thermostatmult> <em> <rad> <etol> <damp>"
    echo "Example: $0 frame def2svp 1 -1 1 Cope_test 298.15 0.999 0 0 50 1.000"
    exit 1
fi

basis="$2"
overall_multiplicity="$3"
ligand_charge="$4"
ligand_mult="$5"
title="$6"
temp="$7"
thermostatmult="$8"
em="$9"
rad="${10}"
etol="${11}"
damp="${12}"

for dir in "$1"*/; do
    cd "$dir"

    fill_fields=$(python3 <<'EOF'
from glob import glob

method = None
overall_charge = None   
highlevel = 0

for file in glob("*.com"):
    with open(file, "r") as f:
        lines = f.readlines()
                        
    for line in lines:
        split_line = line.split()

        if "oniom(" in line.lower():
            first_split = line.split("/")[0]
                                
            method = first_split.split("(")[1]

        elif overall_charge is None and len(split_line) == 6 and all(i.lstrip("+-").isdigit() for i in split_line):
            overall_charge = split_line[0]

        elif len(split_line) == 6 and split_line[-1] == "H":
            highlevel += 1

    break

if method is None:
    raise ValueError("No ONIOM method was found.")

if overall_charge is None:
    raise ValueError("No charge/multiplicity line was found.")

print(f"{method} {overall_charge} {highlevel}")
EOF
    )
    cd ..
    break
done

read -r method overall_charge highlevel <<< "$fill_fields"

sed -e "s/theoryx/$method/g" -i progdyn.conf
sed -e "s/basisx/$basis/g" -i progdyn.conf
sed -e "s/charge Null/charge $overall_charge/g" -i progdyn.conf
sed -e "s/multiplicity Null/multiplicity $overall_multiplicity/g" -i progdyn.conf
sed -e "s/oniomchargemult Null Null Null Null/oniomchargemult $ligand_charge $ligand_mult $ligand_charge $ligand_mult/g" -i progdyn.conf
sed -e "s/example_title/$title/g" -i progdyn.conf
sed -e "s/temperature Null/temperature $temp/g" -i progdyn.conf
sed -e "s/thermostatmult Null/thermostatmult $thermostatmult/g" -i progdyn.conf
sed -e "s/highlevel Null/highlevel $highlevel/g" -i progdyn.conf
sed -e "s/empiricaldispersion Null/empiricaldispersion $em/g" -i progdyn.conf
sed -e "s/radiusmultiplier Null/radiusmultiplier $rad/g" -i progdyn.conf
sed -e "s/etolerance Null/etolerance $etol/g" -i progdyn.conf
sed -e "s/damping Null/damping $damp/g" -i progdyn.conf