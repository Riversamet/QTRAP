#!/usr/bin/env bash
set -euo pipefail

# Check the status of a submitted SGE job on Hoffman2. qstat reports queued
# or running jobs; qacct reports finished jobs, including exit status and
# actual runtime (used to tell a walltime kill apart from a real failure).
#
# Inputs:
#   REMOTE_HOST (environment variable)
#   job_id
#
# Outputs:
#   qstat and qacct output printed to screen

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <job_id>"
    exit 1
fi

if [ -z "${REMOTE_HOST:-}" ]; then
    echo "Error: Set REMOTE_HOST."
    echo "Example: export REMOTE_HOST=you@hoffman2.idre.ucla.edu"
    exit 1
fi

job_id="$1"

echo "--- qstat ---"
ssh "$REMOTE_HOST" "qstat -j $job_id" 2>&1 || echo "(not in qstat -- already left the queue)"

echo "--- qacct ---"
ssh "$REMOTE_HOST" "qacct -j $job_id" 2>&1 || echo "(not yet in qacct -- accounting can lag briefly after completion)"
