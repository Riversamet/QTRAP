#!/usr/bin/env bash
set -euo pipefail

# Generate Gaussian hpmodes frequency input files from completed ONIOM
# optimization outputs.
#
# Inputs:
#   filename pattern
#   ONIOM .out files with matching .com files
#
# Outputs:
#   *-traj.com hpmodes frequency input files

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <filename_pattern>"
    echo "Example: $0 oniom"
    exit 1
fi

pattern="$1"

shopt -s nullglob

for file in *"$pattern"*.out; do
    newname="${file%.out}"

    oniomlog.pl \
        -oi \
        -t "$newname.com" \
        -i "$file" \
        -fo "$newname-traj.com" \
        -fn
done

# Convert optimization inputs into hpmodes frequency inputs for Progdyn sampling.
sed -e "s/opt=(quadmac,calcfc,ts,maxstep=5,noeigentest) freq=noraman/freq=hpmodes/g" -i *-traj.com

# Remove keywords that are not needed or may interfere with hpmodes frequency jobs.
sed -e "s/scf=(xqc,intrep,maxconventionalcyc=80) //g" -i *-traj.com
sed -e "s/nosymm //g" -i *-traj.com
sed -e "s|iop(2/15=3) ||g" -i *-traj.com

echo "Generated hpmodes frequency input files."
