"""Fit + plot for the Rabi frequency calibration sweep.

Pairs with
`qubit_thermometry.workflow.experiments.rabi_frequency_calibration.run_rabi_frequency_calibration_sweep`.
Ported from `Workflow-v1.7.3.json` cells 78 (g-e) and 154 (e-f mirror): a
linear fit of pi-pulse amplitude vs. `1 / drive_length` (a proxy for Rabi
frequency scaling with drive length).
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from uncertainties import unumpy as unp


def fit_and_plot_rabi_frequency_calibration(
    drive_lengths, fitted_pi_amplitudes, transition: str, get_path_to_file
):
    """Linear-fit pi-pulse amplitude vs. `1 / drive_length`, with a summary plot.

    Arguments:
        drive_lengths: The swept drive-pulse lengths (s).
        fitted_pi_amplitudes: The fitted pi-pulse amplitudes returned by
            `run_rabi_frequency_calibration_sweep`, one per drive length.
            May carry uncertainties (`uncertainties.ufloat`); only the
            nominal values are used for the fit/plot, matching the original
            notebook cells.
        transition: `"ge"` or `"ef"`, used in the plot labels and saved file name.
        get_path_to_file: A `helper.setup.get_path_to_file` bound to the
            notebook's `data_root_directory` (e.g. via `functools.partial`).

    Returns:
        `(rabi_slope, rabi_intercept, fig, ax, file_path)`.
    """
    x = (1 / np.asarray(drive_lengths)).astype("float64")
    y = unp.nominal_values(fitted_pi_amplitudes).astype("float64")

    rabi_freq_calib_popt, _rabi_freq_calib_pcov = np.polyfit(x, y, 1, cov=True)
    rabi_slope, rabi_intercept = rabi_freq_calib_popt

    print("Rabi amplitude-length slope:", rabi_slope)
    print("Rabi amplitude-length intercept:", rabi_intercept)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(x * 1e-6, y, ".k")
    ax.plot(x * 1e-6, np.polyval(rabi_freq_calib_popt, x), "-r")
    ax.set_xlabel("1 / drive length (1/us)")
    ax.set_ylabel(f"{transition} pi-pulse amplitude (a.u.)")
    ax.set_title("Rabi frequency calibration")

    file_path = get_path_to_file(f"Rabi_freq_calib_{transition}_", ".png")
    fig.savefig(
        file_path,
        dpi=600,
        format="png",
        metadata=None,
        bbox_inches=None,
        pad_inches=0.1,
        facecolor="auto",
        edgecolor="auto",
        backend=None,
    )
    return rabi_slope, rabi_intercept, fig, ax, file_path
