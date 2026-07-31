"""
QTRAP analysis package.

This package provides reusable analysis functions for QM/MM dynamics trajectory
classification, per-residue RMSD analysis, and partial decomposition analysis.
"""

from .coordinate_tracking import (
    plot_coordinate_outcomes_one_constraint,
    plot_coordinate_outcomes_multi_constraint,
)

from .rmsd import per_residue_RMSD

from .partial_decomposition_analysis import (
    partial_decomposition_analysis_separate,
    partial_decomposition_analysis_combined,
)

__version__ = "1.0.0"
