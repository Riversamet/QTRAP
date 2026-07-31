"""
Coordinate tracking and trajectory outcome classification.

These functions measure distances, angles, or dihedral angles over QM/MM
trajectory files and classify each trajectory according to user-defined
geometric thresholds.

Inputs:
    Amber NetCDF trajectories (*.nc), or Progdyn .xyz trajectories (*.xyz)
    Matching Amber topology files (*.parm7 or *.prmtop)
    pytraj masks defining distances, angles, or dihedrals
    Threshold strings such as "greater than 2.5" or "less than 1.7"

Outputs:
    Matplotlib coordinate vs. time plots
    Lists of trajectories and assigned product/reactant labels
"""

from glob import glob

import matplotlib.pyplot as plt
import numpy as np
import pytraj as pt


def _measure_coordinate(traj, mask):
    """
    Measure a distance, angle, or dihedral from a trajectory.

    The number of atom selections in the mask determines which pytraj
    function is used:
        2 atoms = distance
        3 atoms = angle
        4 atoms = dihedral
    """
    num_atoms = len(mask.split())

    if num_atoms == 2:
        values = pt.distance(traj, mask)
        ylabel = "Distance (Å)"

    elif num_atoms == 3:
        values = pt.angle(traj, mask)
        ylabel = "Angle (degrees)"

    elif num_atoms == 4:
        values = pt.calc_dihedral(traj, mask)
        ylabel = "Dihedral Angle (degrees)"

    else:
        raise ValueError(
            "Each mask must contain 2 atoms for a distance, "
            "3 atoms for an angle, or 4 atoms for a dihedral."
        )

    return values, ylabel


def _threshold_crossed(values, threshold, use_abs=False):
    """
    Check whether any value crosses a user-defined threshold.

    Threshold format:
        "greater than 2.5"
        "less than 1.7"
    """
    words = threshold.split()

    if len(words) != 3 or words[1] != "than":
        raise ValueError(
            "Thresholds must be formatted as 'greater than value' or "
            "'less than value'."
        )

    direction = words[0]
    cutoff = float(words[2])

    if direction not in ["greater", "less"]:
        raise ValueError("Threshold direction must be 'greater' or 'less'.")

    for value in values:
        if use_abs:
            value = np.abs(value)

        if direction == "greater" and value > cutoff:
            return True

        if direction == "less" and value < cutoff:
            return True

    return False


def _threshold_array(values, threshold, use_abs=False):
    """
    Convert a coordinate trace into a binary threshold array.

    Each entry is 1 if that frame satisfies the threshold and 0 otherwise.
    This is used for multi-constraint classification, where all required
    constraints must be satisfied in the same frame.
    """
    words = threshold.split()

    if len(words) != 3 or words[1] != "than":
        raise ValueError(
            "Thresholds must be formatted as 'greater than value' or "
            "'less than value'."
        )

    direction = words[0]
    cutoff = float(words[2])

    if direction not in ["greater", "less"]:
        raise ValueError("Threshold direction must be 'greater' or 'less'.")

    threshold_values = np.zeros(len(values))

    for i, value in enumerate(values):
        if use_abs:
            value = np.abs(value)

        if direction == "greater" and value > cutoff:
            threshold_values[i] = 1

        elif direction == "less" and value < cutoff:
            threshold_values[i] = 1

    return threshold_values


def _convert_xyz_to_nc(traj_dir):
    """
    Convert .xyz trajectory files to Amber NetCDF trajectory files.

    Each .xyz file is matched to a topology file by removing the "-oniom*"
    portion of the filename and adding ".parm7". If you are not following 
    this naming convention, you must edits these scripts to account for this.
    """
    import mdtraj as md

    xyz_files = sorted(glob(f"{traj_dir}/*.xyz"))

    for xyz_file in xyz_files:
        base = xyz_file.split("-oniom")[0]
        topology_file = base + ".parm7"

        traj = md.load_xyz(xyz_file, top=topology_file)

        name = xyz_file.replace(".xyz", "")
        out_nc = f"{name}.nc"
        traj.save_netcdf(out_nc)


def plot_coordinate_outcomes_one_constraint(
    traj_dir,
    masks_list,
    trans_names_list,
    thresholds,
    colors_list,
    trajfiletype,
    abs_list=None,
):
    """
    Plot trajectory coordinate changes and classify trajectory outcomes.

    This version is useful when any one coordinate crossing its threshold is
    enough to define a product or reactant outcome. This is also especially 
    useful when more than two products can form from the same 
    transition-state ensemble.
    
    This function generates one plot for each coordinate being tracked.

    Returns:
        product_trajectories:
            Trajectory files classified as products or reactants.
        product_labels:
            Outcome labels corresponding to product_trajectories.
    """
    if not (
        len(masks_list)
        == len(trans_names_list)
        == len(thresholds)
        == len(colors_list)
    ):
        raise ValueError(
            "masks_list, trans_names_list, thresholds, and colors_list must "
            "have the same length."
        )

    num_transforms = len(masks_list)

    plot_colors = []
    line_styles = []
    trajectory_labels = []
    ylabels = [None for _ in range(num_transforms)]

    product_trajectories = []
    product_labels = []

    coordinate_values = {}

    for i in range(num_transforms):
        coordinate_values[f"all_{i}"] = []

    if abs_list is None:
        abs_list = [False] * num_transforms

    if len(abs_list) != num_transforms:
        raise ValueError("abs_list must have the same length as masks_list.")

    # Convert .xyz trajectories before loading with pytraj.
    if trajfiletype == "xyz":
        _convert_xyz_to_nc(traj_dir)

    traj_files = sorted(glob(f"{traj_dir}/*.nc"))

    for traj_file in traj_files:
        base = traj_file.split("-oniom")[0]
        topology_file = base + ".parm7"
        traj = pt.load(traj_file, top=topology_file)

        # Default assignment if no product/reactant threshold is crossed.
        color = "blue"
        line_style = "dashed"
        label = "No reactant/intermediate or product formed"

        # Each mask defines one diagnostic coordinate.
        for i, (mask, threshold, trans_name, color_choice, use_abs) in enumerate(
            zip(masks_list, thresholds, trans_names_list, colors_list, abs_list)
        ):
            values, ylabel = _measure_coordinate(traj, mask)
            coordinate_values[f"all_{i}"].append(values)
            ylabels[i] = ylabel

            if _threshold_crossed(values, threshold, use_abs=use_abs):
                color = color_choice
                line_style = "solid"
                label = trans_name

        plot_colors.append(color)
        line_styles.append(line_style)
        trajectory_labels.append(label)

        # Only return trajectories that actually formed a product/reactant.
        if color != "blue":
            product_trajectories.append(traj_file)
            product_labels.append(label)

    # Plot one coordinate trace figure for each diagnostic coordinate.
    for i, trans_name in enumerate(trans_names_list):
        plt.figure(figsize=(5, 3))
        plt.xlabel("Time (fs)")
        plt.ylabel(ylabels[i])
        plt.title(f"{trans_name} formation over time")

        labels_seen = []

        for values, color, line_style, label in zip(
            coordinate_values[f"all_{i}"],
            plot_colors,
            line_styles,
            trajectory_labels,
        ):
            if label not in labels_seen:
                plt.plot(values, c=color, linestyle=line_style, label=label)
                labels_seen.append(label)
            else:
                plt.plot(values, c=color, linestyle=line_style)

        plt.legend()

    return product_trajectories, product_labels


def plot_coordinate_outcomes_multi_constraint(
    traj_dir,
    masks_list_forwards,
    masks_list_backwards,
    trans_name_forwards,
    trans_name_backwards,
    thresholds_forwards,
    thresholds_backwards,
    color_forwards,
    color_backwards,
    trajfiletype,
    add_text_forwards=None,
    add_text_backwards=None,
    abs_list_forwards=None,
    abs_list_backwards=None,
):
    """
    Plot trajectory coordinate changes and classify outcomes using multiple
    simultaneous constraints.

    A forward product is assigned only when all forward constraints are
    satisfied in the same frame. If the forward product is not assigned, the
    same logic is applied to the backward/reactant constraints.

    This version is useful when product formation depends on multiple
    coordinate changes occurring together.

    This function generates one plot for each coordinate being tracked.

    Returns:
        product_trajectories:
            Trajectory files classified as products or reactants.
        product_labels:
            Outcome labels corresponding to product_trajectories.
    """
    if len(masks_list_forwards) != len(thresholds_forwards):
        raise ValueError(
            "masks_list_forwards and thresholds_forwards must have the same length."
        )

    if len(masks_list_backwards) != len(thresholds_backwards):
        raise ValueError(
            "masks_list_backwards and thresholds_backwards must have the same length."
        )

    num_forward_coordinates = len(masks_list_forwards)
    num_backward_coordinates = len(masks_list_backwards)

    plot_colors = []
    line_styles = []
    trajectory_labels = []
    ylabels_f = [None for _ in range(num_forward_coordinates)]
    ylabels_b = [None for _ in range(num_backward_coordinates)]

    product_trajectories = []
    product_labels = []

    forward_values = {}
    backward_values = {}

    for i in range(num_forward_coordinates):
        forward_values[f"all_{i}"] = []

    for i in range(num_backward_coordinates):
        backward_values[f"all_{i}"] = []

    if abs_list_forwards is None:
        abs_list_forwards = [False] * num_forward_coordinates

    if abs_list_backwards is None:
        abs_list_backwards = [False] * num_backward_coordinates

    # Convert .xyz trajectories before loading with pytraj.
    if trajfiletype == "xyz":
        _convert_xyz_to_nc(traj_dir)

    traj_files = sorted(glob(f"{traj_dir}/*.nc"))

    for traj_file in traj_files:
        base = traj_file.split("-oniom")[0]
        topology_file = base + ".parm7"
        traj = pt.load(traj_file, top=topology_file)

        forward_thresholds = np.zeros((len(traj), num_forward_coordinates))
        backward_thresholds = np.zeros((len(traj), num_backward_coordinates))

        # Evaluate all forward constraints for each frame.
        for i, (mask, threshold, use_abs) in enumerate(
            zip(masks_list_forwards, thresholds_forwards, abs_list_forwards)
        ):
            values, ylabel = _measure_coordinate(traj, mask)
            forward_values[f"all_{i}"].append(values)
            ylabels_f[i] = ylabel

            forward_thresholds[:, i] = _threshold_array(
                values, threshold, use_abs=use_abs
            )

        # Evaluate all backward/reactant constraints for each frame.
        for i, (mask, threshold, use_abs) in enumerate(
            zip(masks_list_backwards, thresholds_backwards, abs_list_backwards)
        ):
            values, ylabel = _measure_coordinate(traj, mask)
            backward_values[f"all_{i}"].append(values)
            ylabels_b[i] = ylabel

            backward_thresholds[:, i] = _threshold_array(
                values, threshold, use_abs=use_abs
            )

        forward_formed = False
        backward_formed = False

        # Product formation requires all constraints to be satisfied in the
        # same frame, so each row represents one trajectory frame.
        for row in forward_thresholds:
            if np.all(row):
                forward_formed = True
                break

        if not forward_formed:
            for row in backward_thresholds:
                if np.all(row):
                    backward_formed = True
                    break

        if forward_formed:
            color = color_forwards
            line_style = "solid"
            label = trans_name_forwards
            product_trajectories.append(traj_file)
            product_labels.append(label)

        elif backward_formed:
            color = color_backwards
            line_style = "solid"
            label = trans_name_backwards
            product_trajectories.append(traj_file)
            product_labels.append(label)

        else:
            color = "blue"
            line_style = "dashed"
            label = f"Neither {trans_name_forwards} nor {trans_name_backwards} formed"

        plot_colors.append(color)
        line_styles.append(line_style)
        trajectory_labels.append(label)

    # Plot forward coordinate traces.
    if add_text_forwards is not None:
        for i, text in zip(range(num_forward_coordinates), add_text_forwards):
            plt.figure()
            plt.xlabel("Time (fs)")
            plt.ylabel(ylabels_f[i])
            plt.title(f"{trans_name_forwards} formation over time ({text})")

            labels_seen = []

            for values, color, line_style, label in zip(
                forward_values[f"all_{i}"],
                plot_colors,
                line_styles,
                trajectory_labels,
            ):
                if label not in labels_seen:
                    plt.plot(values, c=color, linestyle=line_style, label=label)
                    labels_seen.append(label)
                else:
                    plt.plot(values, c=color, linestyle=line_style)

            plt.legend()

    else:
        for i in range(num_forward_coordinates):
            plt.figure()
            plt.xlabel("Time (fs)")
            plt.ylabel(ylabels_f[i])
            plt.title(f"{trans_name_forwards} formation over time")

            labels_seen = []

            for values, color, line_style, label in zip(
                forward_values[f"all_{i}"],
                plot_colors,
                line_styles,
                trajectory_labels,
            ):
                if label not in labels_seen:
                    plt.plot(values, c=color, linestyle=line_style, label=label)
                    labels_seen.append(label)
                else:
                    plt.plot(values, c=color, linestyle=line_style)

            plt.legend()

    # If forward and backward masks are the same, the forward plots already
    # display the relevant monitored coordinates.
    if masks_list_forwards != masks_list_backwards:
    
        if add_text_backwards is not None:
            for i, text in zip(range(num_backward_coordinates), add_text_backwards):
                plt.figure()
                plt.xlabel("Time (fs)")
                plt.ylabel(ylabels_b[i])
                plt.title(f"{trans_name_backwards} formation over time ({text})")

                labels_seen = []

                for values, color, line_style, label in zip(
                    backward_values[f"all_{i}"],
                    plot_colors,
                    line_styles,
                    trajectory_labels,
                ):
                    if label not in labels_seen:
                        plt.plot(values, c=color, linestyle=line_style, label=label)
                        labels_seen.append(label)
                    else:
                        plt.plot(values, c=color, linestyle=line_style)

                plt.legend()

        else:
            for i in range(num_backward_coordinates):
                plt.figure()
                plt.xlabel("Time (fs)")
                plt.ylabel(ylabels_b[i])
                plt.title(f"{trans_name_backwards} formation over time")

                labels_seen = []

                for values, color, line_style, label in zip(
                    backward_values[f"all_{i}"],
                    plot_colors,
                    line_styles,
                    trajectory_labels,
                ):
                    if label not in labels_seen:
                        plt.plot(values, c=color, linestyle=line_style, label=label)
                        labels_seen.append(label)
                    else:
                        plt.plot(values, c=color, linestyle=line_style)

                plt.legend()

    return product_trajectories, product_labels
