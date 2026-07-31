#!/usr/bin/env bash
set -euo pipefail

# Prepare and run Progdyn QM/MM dynamics jobs for matching structure directories.
#
# Inputs:
#   directory pattern
#   Directory containing Progdyn
#   Progdyn template files
#   freqinHP source output files
#   AtomAmber and methodfile files
#
# Outputs:
#   prepared Progdyn dynamics job directories
#   jobs submitted to compute cluster

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <directory_pattern> <progdyn_dir>"
    echo "Example: $0 frame $HOME/bin/progdyn"
    exit 1
fi

pattern="$1"
progdyn_dir="$2"

shopt -s nullglob

for dir in *"$pattern"*/; do
    cp prog* "$dir"

    cd "$dir"

    mv *.out freqinHP

    method_lines=$(wc -l < methodfile)
    sed -e "s/xxxx/${method_lines}/g" -i progdyn.conf

    "${progdyn_dir}/makedynjobnew" "$progdyn_dir" <<EOF
24
1
10
yes
EOF

    echo "Prepared files for Progdyn in $dir"

    cd ..
done

