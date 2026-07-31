#!/usr/bin/env bash
set -euo pipefail

# Check Gaussian hpmodes frequency outputs for normal termination and move
# successful outputs to the frequency-revision step.
#
# Inputs:
#   *traj.out Gaussian output files
#
# Outputs:
#   successful outputs moved to the next workflow step
#   completion and failure summaries printed to screen

next_step_dir="../step8"

complete_log="complete.txt"
incomplete_log="incomplete.txt"

: > "$complete_log"
: > "$incomplete_log"

shopt -s nullglob

for file in *traj.out; do
    if grep -q "Normal termination" "$file"; then
        echo "$file terminated normally." >> "$complete_log"
	mv "$file" "$next_step_dir/"
    else
        echo "$file had a problem. Check output file." >> "$incomplete_log"
    fi
done

echo "===================="
echo "Frequency job check:"
echo ""
echo "SUCCESS:"
echo ""
cat "$complete_log"
echo ""
echo "FAIL:"
echo ""
cat "$incomplete_log"
echo ""
echo "===================="

rm -f "$complete_log" "$incomplete_log"
