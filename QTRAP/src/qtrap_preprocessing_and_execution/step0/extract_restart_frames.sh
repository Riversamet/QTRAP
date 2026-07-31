#!/usr/bin/env bash
set -euo pipefail

# Extract selected restart frames with velocities from an Amber NetCDF trajectory. 
# 
# Inputs: 
#   Amber topology file 
#   Amber NetCDF trajectory 
#   start frame, end frame, and stride 
# 
# Outputs: 
#   frame_<frame>.rst restart files

if [ "$#" -ne 5 ]; then
    echo "Usage: $0 <topology.prmtop> <trajectory.nc> <start_frame> <end_frame> <stride>"
    exit 1
fi

topology="$1"
trajectory="$2"
start_frame="$3"
end_frame="$4"
stride="$5"

module load amber

for frame in $(seq "$start_frame" "$stride" "$end_frame"); do
    output="frame_${frame}.rst"

    cpptraj << EOF
parm ${topology}
trajin ${trajectory}
trajout ${output} restart onlyframes ${frame} velocities
run
EOF

    echo "Wrote ${output}"
done
