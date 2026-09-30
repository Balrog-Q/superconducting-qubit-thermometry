"""Analysis (fitting + plotting) for the Fast Flux Drive experiments.

Covers four original notebook sections:

- `## Flux Amplitude Calibration` + `## Flux Pulse Check` (they share the
  same 2D heatmap and, for the calibration, a fit of the flux-amplitude ->
  qubit-frequency-shift oscillation).
- `## Decay with Different Flux Detuning` (T1-vs-flux-amplitude fit/plot,
  reused by `## T1 and Population vs. Flux Simultaneously`).
- `## Population with Flux Drive` (effective-temperature-vs-flux-amplitude,
  also reused by `## T1 and Population vs. Flux Simultaneously`).

There is no `analysis_workflow` for these experiments (matching
`workflow.experiments.flux_amplitude_calibration.FastFluxWorkflowOptions`):
every function here is a plain fitting/plotting helper called directly from
the notebook after an `experiment_workflow` (or a sweep of them) has run.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit

from qubit_thermometry.helper.fitting import auto_T1_fit, func_osc
from qubit_thermometry.helper.plotting import plot_2d, plot_temp_single
from qubit_thermometry.helper.temperature import (
    get_ABC_parallel,
    get_qubit_temperature_parameters,
    get_temperature,
)


def plot_flux_heatmap(x, y, z, xlabel, ylabel, title, cmap="Reds", flip=False):
    """Generic flux-drive heatmap: `helper.plotting.plot_2d` plus labels/title.

    Used for the flux-amplitude-calibration map, the flux-pulse-check map,
    and the fast-flux-decay map (old cells' ad hoc `plot_2d(...)` +
    `ax.set_xlabel/set_ylabel/set_title(...)`).
    """
    fig, ax = plt.subplots()
    plot_2d(x, y, z, flip=flip, cmap=cmap, ax=ax)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    return fig, ax


def correct_flux_calibration(flux_freq_results):
    """Subtract the last (highest-flux-amplitude) row from every row.

    Old `flux_freq_results_arr_corr = flux_freq_results_arr - flux_freq_results_arr[-1, :]`.
    """
    return flux_freq_results - flux_freq_results[-1, :]


def fit_flux_calibration(
    flux_amplitudes, detuning_sweep, flux_freq_results_corr,
    resonance_frequency_ge, p0=(1, 0, 2, 5.5),
):
    """Fit the flux-amplitude -> qubit-frequency-shift oscillation.

    For every flux amplitude, the detuning at which `flux_freq_results_corr`
    peaks in magnitude is taken as the (frequency-shifted) qubit frequency,
    then `helper.fitting.func_osc` is fit to amplitude vs. frequency shift.

    Returns `(popt, pcov, x, y)` with `x` the flux amplitudes and `y` the
    frequency shift in GHz (old cell: `amp_max_idx = np.argmax(...)`
    followed by `curve_fit(func_osc, x, y, p0=[1, 0, 2, 5.5])`).
    """
    amp_max_idx = np.argmax(np.abs(flux_freq_results_corr), axis=0)
    f_max = detuning_sweep[amp_max_idx]
    x = np.asarray(flux_amplitudes)
    y = (resonance_frequency_ge - f_max) * 1e-9
    popt, pcov = curve_fit(func_osc, x, y, p0=list(p0))
    return popt, pcov, x, y


def plot_flux_calibration_fit(x, y, popt, qubit_uid):
    """Plot the flux-amplitude-calibration fit (old cell 413 plot)."""
    fig, ax = plt.subplots()
    ax.plot(x, y, ".k")
    ax.plot(x, func_osc(x, *popt), "-r")
    ax.set_xlabel("Flux drive amplitude, a.u.")
    ax.set_ylabel("Qubit frequency, GHz")
    ax.set_title(f"Flux drive calibration fit - {qubit_uid}")
    return fig, ax


def fit_t1_vs_flux(delays, decay_results, data_type="rot"):
    """Fit a T1 decay curve for every flux-amplitude row of `decay_results`.

    Thin wrapper around `helper.fitting.auto_T1_fit` (old cells 431/460).
    Returns `(popt_array, pcov_array)`.
    """
    return auto_T1_fit(delays, decay_results, data_type=data_type, plot=False)


def plot_t1_vs_flux(flux_amp_sweep, popt_t1_arr, qubit_uid, ylim=None):
    """Plot fitted T1 (in us) vs. flux amplitude (old cells 431/460)."""
    fig, ax = plt.subplots()
    ax.plot(flux_amp_sweep, 1e6 / popt_t1_arr[:, 0])
    if ylim is not None:
        ax.set_ylim(*ylim)
    ax.set_ylabel("T1, mks")
    ax.set_xlabel("Flux amplitude, a.u.")
    ax.set_title(f"T1 vs. flux amplitude - {qubit_uid}")
    return fig, ax


def analyze_population_vs_flux(pop_flux_results, qubit, flux_amp_sweep):
    """Effective temperature vs. flux amplitude from the six population traces.

    Old cells 449/459: `get_ABC_parallel` -> `get_temperature` ->
    `plot_temp_single`. Returns `(f_q, anharm, ABC, TABC, fig, ax)`.
    """
    f_q, anharm = get_qubit_temperature_parameters(qubit)
    ABC = get_ABC_parallel(pop_flux_results)
    TABC = get_temperature(ABC, f_q, anharm, three_levels=True)
    fig, ax = plot_temp_single(TABC, xdata=flux_amp_sweep, xlabel="Flux amplitude, a.u.")
    return f_q, anharm, ABC, TABC, fig, ax


def plot_population_iq(pop_flux_results, qubit_uid, label="x0"):
    """IQ scatter of one population sequence vs. flux amplitude (old cell 450)."""
    fig, ax = plt.subplots()
    ax.plot(pop_flux_results[label].real, pop_flux_results[label].imag, "o-")
    ax.set_xlabel("Real part, a.u.")
    ax.set_ylabel("Imaginary part, a.u.")
    ax.set_title(f"Population with flux drive - IQ, {label} - {qubit_uid}")
    return fig, ax
