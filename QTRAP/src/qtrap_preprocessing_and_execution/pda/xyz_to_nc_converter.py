#!/usr/bin/env python3

"""
Convert ONIOM trajectory XYZ files to Amber NetCDF trajectory files.

Each trajectory is matched to an Amber topology file based on the trajectory
filename.

Inputs:
    ONIOM trajectory .xyz files
    matching .parm7 topology files

Outputs:
    Amber NetCDF .nc trajectory files
"""

from pathlib import Path
import mdtraj as md

xyz_files = sorted(Path(".").glob("*.xyz"))

for xyz_file in xyz_files:

    # Determine the corresponding topology file from the trajectory name.

    dyn_base = xyz_file.name.split("-oniom")[0]
    base = dyn_base.replace("forward_dyn_", "").replace("reverse_dyn_", "")
    top_file = Path(f"{base}.parm7")

    if not top_file.exists():
        print(f"Skipping {xyz_file}: topology file {top_file} not found.")
        continue

    # Load trajectory and save as NetCDF.

    traj = md.load_xyz(str(xyz_file), top=str(top_file))

    out_nc = xyz_file.with_suffix(".nc")
    traj.save_netcdf(str(out_nc))

print("All files converted from xyz to nc.")
