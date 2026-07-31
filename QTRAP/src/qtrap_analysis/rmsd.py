"""
Per-residue RMSD analysis for QM/MM dynamics trajectories.

This module identifies residues that repeatedly deviate beyond a chosen RMSD
threshold across trajectory endpoints.

Inputs:
    Amber NetCDF trajectories (*.nc), or ONIOM .xyz trajectories (*.xyz)
    Matching Amber topology files (*.parm7 or *.prmtop)
    pytraj masks for global alignment and per-residue RMSD measurement

Outputs:
    Matplotlib frequency-residue plot
"""

from collections import Counter
from glob import glob
import os

import matplotlib.pyplot as plt
import numpy as np
import pytraj as pt

from .coordinate_tracking import _convert_xyz_to_nc


def per_residue_RMSD(
    traj_dir,
    overall_mask,
    res_mask,
    threshold,
    trajfiletype,
    print_threshold=10,
    min_frames=50,
    reference_frames=20,
):
    """
    Count residues whose endpoint RMSD exceeds a user-defined threshold.

    Each trajectory is first aligned with the supplied overall_mask. A mean
    reference structure is generated from the first reference_frames frames.
    The trajectory is then realigned to that mean structure, and the average
    RMSD for each residue is calculated over the final reference_frames frames.

    Residues whose average endpoint RMSD exceeds the threshold are counted 
    across all trajectories.
    """

    # Limit OpenMP threading because pytraj/AmberTools kernels can oversubscribe
    # CPU resources in notebooks or shared HPC environments.
    os.environ["OMP_NUM_THREADS"] = "1"

    residues_above_threshold = []

    if trajfiletype == "xyz":
        _convert_xyz_to_nc(traj_dir)

    traj_files = sorted(glob(f"{traj_dir}/*.nc"))

    for traj_file in traj_files:
        base = traj_file.split("-oniom")[0]
        topology_file = base + ".parm7"
        traj = pt.load(traj_file, top=topology_file)

        # Very short trajectories are skipped because they do not contain
        # enough frames for the reference/endpoint comparison.
        if traj.n_frames < min_frames:
            continue

        # Align the trajectory to its first frame before building an average
        # early-trajectory reference structure.
        aligned_to_first = pt.align(
            traj,
            ref=traj[0],
            mask=overall_mask,
            mass=True,
        )

        reference = pt.mean_structure(
            aligned_to_first,
            frame_indices=range(reference_frames),
        )

        # Realign the original trajectory to the mean reference so per-residue
        # RMSDs measure local deformation rather than global translation/rotation.
        aligned_to_reference = pt.align(
            traj,
            ref=reference,
            mask=overall_mask,
            mass=True,
        )

        # Count non-solvent residues so residue masks can be applied one at a time.
        traj_without_solvent = traj["!(:WAT|:Na+|:Cl-)"]
        n_residues = traj_without_solvent.topology.n_residues

        for residue in range(1, n_residues + 1):
            residue_mask = f":{residue}{res_mask}"

            rmsd_values = pt.rmsd(
                aligned_to_reference[-reference_frames:],
                ref=reference,
                mask=residue_mask,
                nofit=True,
            )

            if np.mean(rmsd_values) > threshold:
                residues_above_threshold.append(str(residue))

    residue_counts = Counter(residues_above_threshold)

    # Print especially frequent deviations so the most important residues are
    # easy to identify in notebook output.
    for residue, count in residue_counts.items():
        if count > print_threshold:
            print(
                f"Residue {residue} shifted by at least "
                f"{threshold} Å {count} times."
            )

    plt.figure(figsize=(11, 9))
    plt.bar(residue_counts.keys(), residue_counts.values())
    plt.ylabel(f"Frequency of RMSD > {threshold} Å")
    plt.xlabel("Residue")
    plt.title("Frequency of Residue Conformational Changes (Averaged Frames)")
    plt.xticks(rotation=45)
    