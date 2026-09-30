"""Plotting and optimal-point selection for the single-shot g/e/f sweeps.

The "Single Shot 0 and 1 Measurements" section of the Population &
Temperature Measurements notebook runs one plain `iq_blobs` measurement and
three near-identical sweeps (vs. drive length, vs. integration delay/length,
vs. readout amplitude/length), each picking the sweep point with the
*highest* g/e/f correct-state-assignment fidelity returned by the
`iq_blobs` analysis workflow. This module factors out the plotting and
optimal-point-selection code that would otherwise be repeated across the
three sweeps.

Complements :mod:`qubit_thermometry.helper.single_shot` (shot collection and
rotation statistics, unchanged) and
:mod:`qubit_thermometry.helper.plotting` (`plot_2d`, used for the sweep
heatmaps).

Ported from `Workflow-v1.7.3.json` cells 226-284.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import norm

from qubit_thermometry.helper.plotting import plot_2d
from qubit_thermometry.helper.single_shot import bimodal, gauss

STATE_LABELS = {"g": "ground", "e": "first excited", "f": "second excited"}
STATE_COLORS = {"g": "b", "e": "r", "f": "y"}
STATE_ALPHAS = {"g": 0.1, "e": 0.1, "f": 0.01}


def pick_optimal_1d(fidelity_arr) -> tuple[int, float]:
    """`(index, value)` of the highest fidelity in a 1D sweep (NaN-aware)."""
    fidelity_arr = np.asarray(fidelity_arr, dtype=float)
    index = int(np.nanargmax(fidelity_arr))
    return index, float(fidelity_arr[index])


def pick_optimal_2d(fidelity_arr) -> tuple[int, int, float]:
    """`(index_0, index_1, value)` of the highest fidelity in a 2D sweep (NaN-aware)."""
    fidelity_arr = np.asarray(fidelity_arr, dtype=float)
    flat_index = int(np.nanargmax(fidelity_arr))
    index_0, index_1 = np.unravel_index(flat_index, fidelity_arr.shape)
    return int(index_0), int(index_1), float(fidelity_arr[int(index_0), int(index_1)])


def print_assignment_matrix(matrix, fidelity: float | None = None) -> None:
    """Print a g/e/f correct-state-assignment matrix (and fidelity, if given)."""
    if matrix is None:
        return
    print("Correct-state-assignment matrix:")
    print(np.round(matrix, 4))
    if fidelity is not None:
        print("Assignment fidelity:", f"{fidelity * 100:0.2f} %")


def plot_iq_scatter(shots_per_state: dict, qubit_uid: str, states: str = "gef"):
    """Scatter of single shots on the IQ plane, plus the per-state means."""
    fig, ax = plt.subplots()
    ax.set_title(f"Single shots on the IQ plane - {qubit_uid}")
    for s in states:
        data = shots_per_state[s]
        ax.plot(
            data.real, data.imag, ".", color=STATE_COLORS[s], alpha=STATE_ALPHAS[s],
            label=STATE_LABELS[s],
        )
    for s in states:
        data = shots_per_state[s]
        ax.plot(np.mean(data.real), np.mean(data.imag), "o", mfc=STATE_COLORS[s], mec="k")
    ax.set_xlabel("Real part, a.u.")
    ax.set_ylabel("Imaginary part, a.u.")
    ax.legend()
    return fig, ax


def plot_iq_histograms(shots_per_state: dict, qubit_uid: str, states: str = "gef", n_bins: int = 50):
    """Real/imag histograms of the single shots of every prepared state."""
    fig, axs = plt.subplots(1, 2, sharey=True, tight_layout=True)
    fig.suptitle(f"Single-shot distributions - {qubit_uid}")
    axs[0].set_title("Real")
    axs[1].set_title("Imag")
    for s in states:
        data = shots_per_state[s]
        axs[0].hist(data.real, bins=n_bins, alpha=0.5, label=STATE_LABELS[s])
        axs[1].hist(data.imag, bins=n_bins, alpha=0.5, label=STATE_LABELS[s])
    axs[0].legend()
    axs[1].legend()
    return fig, axs


def plot_iq_density(zero_data, one_data, qubit_uid: str, n_bins: int = 50):
    """2D histogram (density) of the state-0/state-1 shots on the IQ plane."""
    fig, ax = plt.subplots(tight_layout=True)
    ax.set_title(f"Single-shot density - {qubit_uid}")
    ax.hist2d(zero_data.real, zero_data.imag, n_bins)
    ax.hist2d(one_data.real, one_data.imag, n_bins)
    ax.set_xlabel("Real part, a.u.")
    ax.set_ylabel("Imaginary part, a.u.")
    return fig, ax


def plot_projected_distance_histogram(
    zero_data_proj, one_data_proj, distance: float, qubit_uid: str, n_bins: int = 200
):
    """Relative-distance histogram of the projected (rotated) shots."""
    fig, ax = plt.subplots()
    ax.set_title(f"Projected single shots - {qubit_uid}")
    ax.hist(zero_data_proj / distance, bins=n_bins, alpha=0.5, label=STATE_LABELS["g"])
    ax.hist(one_data_proj / distance, bins=n_bins, alpha=0.5, label=STATE_LABELS["e"])
    ax.axvline(1, color="k", ls="--")
    ax.axvline(-1, color="k", ls="--")
    ax.set_yscale("log")
    ax.set_ylabel("N points")
    ax.set_xlabel("Relative distance")
    ax.legend()
    return fig, ax


def fit_and_plot_gaussian(data, qubit_uid: str, state_label: str = "0", n_bins: int = 200):
    """Single-Gaussian fit of a projected-shots distribution (residual population check)."""
    fig, ax = plt.subplots()
    n, bins, patches = ax.hist(data, bins=n_bins, alpha=0.5, density=True)

    mu, sigma = norm.fit(data)
    y = norm.pdf(bins, mu, sigma)
    ax.plot(bins, y, "r--", linewidth=2)
    ax.set_yscale("log")
    ax.set_ylabel("Probability density")
    ax.set_xlabel("Relative distance")
    ax.set_title(f"Gaussian fit state {state_label}: mu = {mu:.4f}, sigma = {sigma:.4f}")
    print("mu:", mu, " sigma:", sigma)
    return fig, ax, mu, sigma


def fit_and_plot_bimodal(
    data,
    expected,
    qubit_uid: str,
    fit_label: str,
    color: str,
    zero_first: bool = True,
    n_bins: int = 200,
    ylim: tuple[float, float] = (1e-1, 5e3),
):
    """Bimodal (two-Gaussian) fit of a projected-shots distribution.

    Used to extract the residual ground/excited population that leaks into
    the "wrong" state's distribution. `zero_first` selects the label order
    of the two component Gaussians in the legend/printout (`"One"`/`"Zero"`
    vs. the reverse), matching which state's residual is being fit.
    """
    fig, ax = plt.subplots()
    y, x, patches = ax.hist(data, bins=n_bins, color=color, alpha=0.25)
    x = (x[1:] + x[:-1]) / 2

    params, cov = curve_fit(bimodal, x, y, expected)
    sigma = np.sqrt(np.diag(cov))
    x_fit = np.linspace(x.min(), x.max(), 500)

    label_1, label_2 = ("One", "Zero") if zero_first else ("Zero", "One")
    ax.plot(x_fit, bimodal(x_fit, *params), color="green", lw=3, label=f"{label_1}+{label_2}")
    ax.plot(x_fit, gauss(x_fit, *params[:3]), color="red", lw=2, ls="--", label=label_1)
    ax.plot(x_fit, gauss(x_fit, *params[3:]), color="b" if zero_first else "blue", lw=2, ls=":", label=label_2)
    ax.set_yscale("log")
    ax.set_ylabel("N points")
    ax.set_xlabel("Relative distance")
    ax.set_ylim(*ylim)
    ax.set_title(f"Bimodal fit {fit_label} - {qubit_uid}")
    ax.legend()
    print(pd.DataFrame(data={"params": params, "sigma": sigma}, index=bimodal.__code__.co_varnames[1:]))
    plt.show()

    area_ratio = (params[4] * params[5]) / (params[1] * params[2])
    print("Area ratio:", area_ratio if zero_first else 1 / area_ratio)
    return fig, ax, params, sigma


def plot_fidelity_vs_1d(
    x, fidelity_arr, optimal_index: int, xlabel: str, qubit_uid: str, secondary=None
):
    """Assignment fidelity (and optional secondary metric) vs. a single swept parameter.

    `secondary`, if given, is `(y, ylabel)` for a second panel below, plotted
    in log scale (e.g. the diagnostic `rel_std_0`).
    """
    n_axes = 2 if secondary is not None else 1
    fig, ax = plt.subplots(n_axes, 1, sharex=True, figsize=(10, 8 if n_axes == 2 else 5))
    axes = ax if n_axes == 2 else [ax]
    fig.suptitle(f"Single shot vs. {xlabel.lower()} - {qubit_uid}", fontsize=16)
    fig.supxlabel(xlabel)

    axes[0].plot(x, np.asarray(fidelity_arr) * 100, ".k")
    axes[0].set_ylabel("Assignment fidelity, %")

    if secondary is not None:
        y, ylabel = secondary
        axes[1].plot(x, y, ".k")
        axes[1].set_ylabel(ylabel)
        axes[1].set_yscale("log")

    for axis in axes:
        axis.axvline(x=x[optimal_index], ls="-.", color="r", label="optimal (max fidelity)")
        axis.legend()

    return fig, ax


def plot_fidelity_vs_2d_lines(
    x, fidelity_2d, series_values, x_opt: float, xlabel: str, qubit_uid: str,
    legend_title: str, series_fmt: str = "{:.0f}",
):
    """Assignment fidelity vs. one swept parameter, one line per value of a second parameter.

    `fidelity_2d` has shape `(len(x), len(series_values))`.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_title(f"Single shot vs. {xlabel.lower()} - {qubit_uid}")
    for k, series_value in enumerate(series_values):
        ax.plot(x, fidelity_2d[:, k] * 100, ".-", label=series_fmt.format(series_value))
    ax.axvline(x=x_opt, ls="-.", color="r", label="optimal (max fidelity)")
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Assignment fidelity, %")
    ax.legend(title=legend_title, ncol=2 if len(series_values) > 6 else 1)
    return fig, ax


def plot_fidelity_heatmap(
    x, y, z, x_opt: float, y_opt: float, xlabel: str, ylabel: str, qubit_uid: str,
):
    """Heatmap of the assignment fidelity `z` (already `% `-scaled) over `x`/`y`.

    `z` must have shape `(len(x), len(y))` (the convention used by
    `qubit_thermometry.helper.plotting.plot_2d`, which this wraps).
    """
    fig, ax = plot_2d(x, y, z)
    ax.set_title(f"Assignment fidelity - {qubit_uid}")
    ax.plot(x_opt, y_opt, "rx", ms=12, label="optimal")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend()
    return fig, ax
