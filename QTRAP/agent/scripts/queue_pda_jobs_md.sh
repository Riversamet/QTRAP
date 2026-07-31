#!/usr/bin/env bash
set -euo pipefail

# Run partial decomposition analysis on one long MD trajectory.
# This MD workflow skips the QM/MM per-frame xyz-to-nc conversion and
# job queueing steps, since the input is already a continuous trajectory.
# image.in and decomp.in are generated here, and the submitted PDA job
# runs mmpbsa_shortener.py after MMPBSA.py finishes.
#
# Inputs:
#   trajectory (.nc)
#   matching Amber topology (.parm7 or .prmtop)
#   ligand mask, receptor mask, and solvent/ion strip masks
#
# Output:
#   <trajectory>-pda/FINAL_DECOMP_MMPBSA-c.dat

if [ "$#" -lt 5 ]; then
    echo "Usage: $0 <traj.nc> <topology.parm7> <ligand_mask> <receptor_mask> <strip_masks> [stride] [startframe] [endframe] [interval]"
    echo "Example: $0 prod.nc system.parm7 ':149' ':1-148' ':WAT :Na+ :Cl-' 1"
    exit 1
fi

nc_file="$1"
topology="$2"
ligand_mask="$3"
receptor_mask="$4"
strip_masks="$5"
stride="${6:-50}"
startframe="${7:-1}"
interval="${9:-5}"

module load amber

frame_report=$(cpptraj -p "$topology" 2>&1 <<EOF
trajin $nc_file
run
quit
EOF
)

if ! printf "%s\n" "$frame_report" | grep -qi "Coordinate frames"; then
    echo "Error: $nc_file does not appear to match $topology."
    exit 1
fi

total_frames=$(printf "%s\n" "$frame_report" | sed -nE 's/.*, ([0-9]+) frames.*/\1/p')
endframe="${8:-$total_frames}"

bash generate_ligand_enzyme_complex_parm.sh "$topology" "$ligand_mask" "$strip_masks"

cp "$topology" .
bash bondi_radii.sh

topology_bondi="${topology%.parm7}-bondi.parm7"
traj_prefix="${nc_file%.nc}"

job_dir="${traj_prefix}-pda"
mkdir -p "$job_dir"

cp "$nc_file" "$job_dir/"
cp "$topology_bondi" "$job_dir/"
cp complex-bondi.parm7 enzyme-bondi.parm7 ligand-bondi.parm7 "$job_dir/"
cp pda.sh mmpbsa_shortener.py "$job_dir/"

cd "$job_dir"

cat > image.in <<EOF
parm ${topology_bondi}
trajin ${nc_file} 1 last ${stride}

autoimage

rms first ${receptor_mask}

trajout ${traj_prefix}-i.nc

go
EOF

cpptraj -i image.in

print_res="${receptor_mask#:},${ligand_mask#:}"

cat > decomp.in <<EOF
&general
  startframe=${startframe}, endframe=${endframe}, interval=${interval},
  entropy=0,
  verbose=1,
  receptor_mask='${receptor_mask}',
  ligand_mask='${ligand_mask}',
/
&gb
  igb=8, saltcon=0.150,
/
&decomp
  idecomp=4,
  dec_verbose=3,
  print_res="${print_res}"
/
EOF

sed -e "s|xx|${traj_prefix}-i|g" -e "s|xy|$topology_bondi|g" -i pda.sh

# Run the shortener as the last step of the same submitted job, so the
# final output is already shortened by the time the job finishes.
echo "python3 mmpbsa_shortener.py" >> pda.sh

qsub pda.sh

cd ..

echo "MD PDA job submitted from $job_dir."
echo "Once finished, the result is $job_dir/FINAL_DECOMP_MMPBSA-c.dat."