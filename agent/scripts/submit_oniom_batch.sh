#!/usr/bin/env bash
set -euo pipefail

# Batch wrapper for Gsub.py. Submit one or more Gaussian input files
# as Hoffman2 (SGE) jobs.
#
# Not part of src/ -- referenced directly from agent/scripts/, not
# copied into the run's own directory.
#
# Inputs:
#   number of processors
#   walltime in hours
#   one or more Gaussian .com files
#
# Outputs:
#   jobs submitted to the queue via Gsub.py

if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <processors> <walltime_hours> <file1.com> [file2.com ...]"
    echo "Example: $0 24 30 frame_15000-oniom.com"
    echo "Example (batch): $0 24 30 *.com"
    exit 1
fi

if [ -f "Gsub.py" ]; then
    gsub_path="Gsub.py"
else
    gsub_path="../step6/Gsub.py"
fi

processors="$1"
walltime="$2"
shift 2

for com_file in "$@"; do
    if [[ ! -f "$com_file" ]]; then
        echo "Skipping $com_file: file not found."
        continue
    fi

    echo "Submitting $com_file (-p $processors -t $walltime)"
    python "$gsub_path" -p "$processors" -t "$walltime" "$com_file"
done
