#!/usr/bin/env bash
set -euo pipefail

# Run an allowed workflow script on Hoffman2 over SSH.
# Scripts run from either the active run directory, or from the agent/ directory.
#
# Inputs:
#   REMOTE_HOST and REMOTE_BASE_DIR environment variables
#   <dir>/<script_name>, run_name
#   optional script arguments
#
# Outputs:
#   whatever the selected workflow script produces

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/../.env" ]; then
    set -a
    source "$SCRIPT_DIR/../.env"
    set +a
fi

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <dir>/<script_name> <run_name> [args...]"
    exit 1
fi

if [ -z "${REMOTE_HOST:-}" ]; then
    echo "Error: Set REMOTE_HOST."
    echo "Example: export REMOTE_HOST=you@hoffman2.idre.ucla.edu"
    exit 1
fi

if [ -z "${REMOTE_BASE_DIR:-}" ]; then
    echo "Error: Set REMOTE_BASE_DIR."
    echo "Example: export REMOTE_BASE_DIR=/u/home/you/project_directory"
    exit 1
fi

script_ref="$1"
run_name="$2"
shift 2

if [[ "$script_ref" == /* || "$script_ref" == *".."* ]]; then
    echo "Error: '$script_ref' must be a relative path inside the run, with no '..' or leading '/'."
    exit 1
fi

dir_part=$(dirname "$script_ref")
script_name=$(basename "$script_ref")

run_base="runs/$run_name/qtrap_preprocessing_and_execution"
remote_path="$REMOTE_BASE_DIR/$run_base/$dir_part"

case "$script_name" in
    submit_oniom_batch.sh|queue_pda_jobs_md.sh|check_start_files.sh|conf_fill.sh)
        script_path="$REMOTE_BASE_DIR/agent/scripts/$script_name"
        ;;
    *)
        script_path="$script_name"
        ;;
esac

qrsh_dirs=("step0" "step2" "step4")
needs_qrsh=false
for d in "${qrsh_dirs[@]}"; do
    if [ "$dir_part" == "$d" ]; then
        needs_qrsh=true
        break
    fi
done

if [ "$needs_qrsh" == true ]; then
    if [ -z "${QRSH_FLAGS:-}" ]; then
        echo "Error: QRSH_FLAGS is not set in .env. step0/step2/step4 require a compute node via qrsh."
        exit 1
    fi
    ssh "$REMOTE_HOST" "qrsh -l $QRSH_FLAGS \"cd $remote_path && bash $script_path $*\""
else
    ssh "$REMOTE_HOST" "cd $remote_path && bash $script_path $*"
fi