#!/usr/bin/env bash
set -euo pipefail

# Copy QM/MM trajectory files and shared PDA files into forward and reverse
# analysis directories.
#
# Inputs:
#   trajectory .xyz files from the QM/MM dynamics step
#   PDA input, topology, shell, and Python files
#
# Outputs:
#   forward/ and reverse/ PDA working directories

mkdir -p forward
mkdir -p reverse

# Copy forward trajectories

cp ../step10/trajs/forward*.xyz forward/

# Copy reverse trajectories

cp ../step10/trajs/reverse*.xyz reverse/

# Copy shared PDA input and script files

cp *.in forward/
cp *.in reverse/

cp *.parm7 forward/
cp *.parm7 reverse/

cp *.sh forward/
cp *.sh reverse/

cp *.py forward/
cp *.py reverse/
