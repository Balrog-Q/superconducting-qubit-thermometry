"""Shared plotting helpers.

`plot_temperatures`/`plot_temp_single`/`plot_stat`/`plot_rotation_stat` plot
the `A`/`B`/`C` effective-temperature estimators from
:mod:`qubit_thermometry.helper.temperature` and are reused by Population,
Fast Flux Drive and SINIS Calibration. `plot_2d` is a generic heatmap helper
used by Fast Flux Drive.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

_TEMP_COLOR_CYCLE = [
    "red", "orange", "gold", "green", "limegreen", "cyan", "blue", "darkviolet", "magenta",
]


def plot_temperatures(TABC_I, TABC_Q, skip=(), xlim=None, ylim=None):
    """Plot every `A`/`B`/`C` estimator of `TABC_I`/`TABC_Q` vs. point number."""
    fig, ax = plt.subplots(2, 1, sharex=True, figsize=(10, 8))

    ax[0].set_prop_cycle(color=_TEMP_COLOR_CYCLE)
    ax[1].set_prop_cycle(color=_TEMP_COLOR_CYCLE)

    fig.supxlabel("Point number")
    fig.supylabel("Effective temperature, mK")

    ax[0].set_title("I component")
    ax[1].set_title("Q component")

    for k in TABC_I:
        if k in skip:
            continue
        ax[0].plot(TABC_I[k], "o-", label=k)
    ax[0].legend()

    for k in TABC_Q:
        if k in skip:
            continue
        ax[1].plot(TABC_Q[k], "o-", label=k)
    ax[1].legend()

    if xlim is not None:
        ax[0].set_xlim(xlim)
        ax[1].set_xlim(xlim)
    if ylim is not None:
        ax[0].set_ylim(ylim)
        ax[1].set_ylim(ylim)

    return fig, ax


def plot_temp_single(TABC, skip=(), xlim=None, ylim=None, xdata=None, xlabel="Point Number"):
    """Plot every `A`/`B`/`C` estimator of `TABC` vs. `xdata` (or point number)."""
    if xdata is not None:
        assert len(xdata) == len(TABC[next(iter(TABC))]), "Provide xdata array of proper length!"

    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    ax.set_prop_cycle(color=_TEMP_COLOR_CYCLE)

    fig.supxlabel(xlabel)
    fig.supylabel("Effective temperature, mK")

    for k in TABC:
        if k in skip:
            continue
        if xdata is None:
            ax.plot(TABC[k], "o-", label=k)
        else:
            ax.plot(xdata, TABC[k], "o-", label=k)
    ax.legend()

    if xlim is not None:
        ax.set_xlim(xlim)
    if ylim is not None:
        ax.set_ylim(ylim)

    return fig, ax


def plot_stat(STAT_I, STAT_Q):
    """Bar plot of the mean +/- std of every estimator's `STAT_I`/`STAT_Q` mean value."""
    labels = list(STAT_I.keys())

    I_mean = [np.mean(STAT_I[k][0]) for k in labels]
    Q_mean = [np.mean(STAT_Q[k][0]) for k in labels]
    I_err = [np.std(STAT_I[k][0]) for k in labels]
    Q_err = [np.std(STAT_Q[k][0]) for k in labels]

    fig, ax = plt.subplots(1, 2, sharex=True, figsize=(10, 8))
    fig.supylabel("Effective temperature, mK")

    ax[0].set_title("I component")
    ax[1].set_title("Q component")

    ax[0].bar(labels, I_mean)
    ax[0].errorbar(labels, I_mean, yerr=I_err, fmt="o", color="r")

    ax[1].bar(labels, Q_mean)
    ax[1].errorbar(labels, Q_mean, yerr=Q_err, fmt="o", color="r")

    return fig, ax


def plot_rotation_stat(phase_arr, STAT_I, STAT_Q, info_type="rel_err"):
    """3x3 grid of every estimator's `info_type` vs. projection phase.

    `info_type` is one of `"mean"`, `"error"`, `"rel_err"`.
    """
    it, title, ylabel = {
        "mean": (0, "Mean of effective temperature vs. phase rotation", "Effective temperature, mK"),
        "error": (1, "Absolute errors for effective temperature vs. phase rotation", "Absolute error"),
        "rel_err": (2, "Relative errors for effective temperature vs. phase rotation", "Relative error"),
    }[info_type]

    fig, ax = plt.subplots(3, 3, sharex=True, figsize=(10, 8))

    fig.suptitle(title, fontsize=16)
    fig.supylabel(ylabel)
    fig.supxlabel("Phase")

    for row, letter in enumerate(["A", "B", "C"]):
        for col, index in enumerate(["1", "2", "3"]):
            k = f"T{letter}{index}"
            ax[row, col].plot(phase_arr, STAT_I[k][:, it], label="I")
            ax[row, col].plot(phase_arr, STAT_Q[k][:, it], label="Q")
            ax[row, col].set_title(f"{letter}{index}")

    fig.legend(*ax[0, 0].get_legend_handles_labels())

    return fig, ax


def plot_2d(x, y, z, flip=False, cmap="viridis", ax=None):
    """Pseudocolor heatmap of `z` (2D array) over `x`/`y` axes."""
    if ax is None:
        fig, ax = plt.subplots()
    else:
        fig = ax.figure

    data = np.asarray(z).T
    if flip:
        data = np.flipud(data)

    mesh = ax.pcolormesh(x, y, data, cmap=cmap, shading="auto")
    fig.colorbar(mesh, ax=ax)
    return fig, ax
