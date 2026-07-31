#!/usr/bin/env bash
set -euo pipefail

# Create forward and reverse Progdyn setup directories from prepared frame folders.
#
# Inputs:
#   directory pattern
#   prepared frame directories
#   Progdyn configuration files (proganal and progdyn.conf)
#
# Outputs:
#   forward_dyn and reverse_dyn directories

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <directory_pattern>"
    echo "Example: $0 frame"
    exit 1
fi

mkdir -p forward_dyn reverse_dyn

cp qmmm_dyn_prep.sh sort_trajs.sh progdyn.conf proganal forward_dyn/
cp qmmm_dyn_prep.sh sort_trajs.sh progdyn.conf proganal reverse_dyn/

shopt -s nullglob

for dir in *$1*/; do
    cp -r "$dir" forward_dyn/
    mv "$dir" reverse_dyn/
    echo "$dir copied to forward_dyn and reverse_dyn."
done

cd reverse_dyn/
sed -e "s/searchdir positive/searchdir negative/g" -i progdyn.conf
cd ..
