"""Plotting for the Rabi chevron 2D amplitude-vs-detuning sweep.

Pairs with `qubit_thermometry.workflow.experiments.rabi_chevron.run_rabi_chevron_sweep`.
Ported from `Workflow-v1.7.3.json` cells 68-69 (g-e) and 144-145 (e-f mirror).
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np


def plot_chevron_map(amplitudes, detunings, rabi_chevron_arr, transition: str, get_path_to_file):
    """2D `pcolormesh` of the raw signal amplitude vs. drive amplitude and detuning.

    Arguments:
        amplitudes: The swept drive amplitudes (x-axis).
        detunings: The swept frequency detunings, in Hz (y-axis, plotted in MHz).
        rabi_chevron_arr: The raw (complex) signal array returned by
            `run_rabi_chevron_sweep`, shape `(len(detunings), len(amplitudes))`.
        transition: `"ge"` or `"ef"`, used in the title and saved file name.
        get_path_to_file: A `helper.setup.get_path_to_file` bound to the
            notebook's `data_root_directory` (e.g. via `functools.partial`).

    Returns:
        `(fig, ax, file_path)`.
    """
    x = amplitudes
    y = np.asarray(detunings) * 1e-6
    z = np.absolute(rabi_chevron_arr)

    fig, ax = plt.subplots(figsize=(8, 6))
    c = ax.pcolormesh(x, y, z, cmap="Reds", shading="auto")
    fig.colorbar(c, ax=ax, label="Signal amplitude (a.u.)")
    ax.set_xlabel("Drive amplitude (a.u.)")
    ax.set_ylabel("Detuning (MHz)")
    ax.set_title(f"Rabi chevron, {transition}-transition")

    file_path = get_path_to_file(f"Rabi_chevron_{transition}_", ".png")
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
    return fig, ax, file_path
