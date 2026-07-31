#!/usr/bin/env bash
set -euo pipefail

# Report trajectory frame information for queue_pda_jobs.sh.
# Placeholders are replaced by queue_pda_jobs.sh:
#   xx = topology file
#   xy = input trajectory
# Inputs:
#   topology file placeholder replaced by queue_pda_jobs.sh
#   trajectory file placeholder replaced by queue_pda_jobs.sh
#
# Outputs:
#   cpptraj frame information printed to stdout

cpptraj -p xx 2>&1 <<EOF | grep -E "Frames|read|trajin"
trajin xy
run
quit
EOF
