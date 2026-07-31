#!/usr/bin/env bash
set -euo pipefail

# Verify the run's starting structure files exist and match before
# preprocessing begins. If the topology and trajectory are incompatible,
# exit with a clear error instead of failing later in the workflow.
#
# Not part of src/ -- referenced directly from agent/scripts/, run inside
# start_files/.
#
# Inputs:
#   topology filename (e.g. system.prmtop)
#   trajectory filename (e.g. system.nc)
#
# Outputs:
#   Prints a success message and exits 0 if the files match.
#   Prints an error message and exits 1 otherwise.

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <topology_file> <trajectory_file>"
    exit 1
fi

topology="$1"
trajectory="$2"

if [ ! -f "$topology" ]; then
    echo "Error: topology file '$topology' not found."
    exit 1
fi

if [ ! -f "$trajectory" ]; then
    echo "Error: trajectory file '$trajectory' not found."
    exit 1
fi

module load amber

frame_report=$(cpptraj -p "$topology" 2>&1 <<EOF
trajin $trajectory
run
quit
EOF
)

if ! printf "%s\n" "$frame_report" | grep -qi "frames and processed"; then
    echo "Error: $trajectory does not appear to match $topology."
    exit 1
fi

echo "OK: $topology and $trajectory match."