"""Three-level population measurement analysis: plotting and estimator extraction.

Pairs with `qubit_thermometry.workflow.experiments.population`. The bulk of
the pe/pg-estimator and effective-temperature machinery (the full 9
`A`/`B`/`C` estimators, their statistics, projection-phase optimization) is
generic and already lives in `qubit_thermometry.helper.temperature`/
`qubit_thermometry.helper.plotting`; the notebook calls those directly for
the "Single-Point"/"Population Statistics"/"Rotation and Measurement
Optimisation" sections. This module holds the plots/estimators that are
*not* already covered there:

- the population-vs-IQ-plane scatter (used both for the statistics section
  and the vs.-readout-frequency sweep),
- the specific `A1`/`B2`/`C3` estimator combination used for a quick,
  single-run pe/pg and temperature readout (old cell 355),
- the ge-pre-pulse-amplitude estimator (uses a zero-pre-pulse baseline
  correction, old cell 375),
- the vs.-readout-frequency plots and optimal-frequency selection.

Ported from `Workflow-v1.7.3.json` cells 354-355, 374-375, 385-386, 389.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from qubit_thermometry.helper.temperature import T_calc, get_ABC


def plot_iq_projection(results: dict, labels, qubit_uid: str, title: str, fmt: str | None = "o-"):
    """IQ-plane plot of the (complex) population traces named in `labels`."""
    fig, ax = plt.subplots()
    ax.set_title(f"{title} - {qubit_uid}")
    for label in labels:
        data = results[label]
        if fmt is None:
            ax.plot(data.real, data.imag, label=label)
        else:
            ax.plot(data.real, data.imag, fmt, label=label)
    ax.set_xlabel("Real part, a.u.")
    ax.set_ylabel("Imaginary part, a.u.")
    ax.legend()
    return fig, ax


def plot_population_estimators_a1_b2_c3(pop_full_results: dict, f_q, qubit_uid: str):
    """The `A1`/`B2`/`C3` pe/pg and effective-temperature estimators, real and imag.

    Equivalent to projecting `pop_full_results` at phase 0 (`make_projection`)
    and taking `get_ABC(...)["A1"]`/`["B2"]`/`["C3"]` of each of the real
    (labelled `_Q`) and imaginary (labelled `_I`) projections -- this
    specific combination of one estimator from each of the three groups
    cancels a `(y1 - y2)` factor algebraically, so `C3` need not be computed
    as `A3 * B3` here.
    """
    proj_real = {k: v.real for k, v in pop_full_results.items()}
    proj_imag = {k: v.imag for k, v in pop_full_results.items()}
    abc_real = get_ABC(proj_real)
    abc_imag = get_ABC(proj_imag)

    A_real, B_real, C_real = abc_real["A1"], abc_real["B2"], abc_real["C3"]
    A_imag, B_imag, C_imag = abc_imag["A1"], abc_imag["B2"], abc_imag["C3"]

    fig_pe, ax_pe = plt.subplots()
    ax_pe.plot(C_real, "-o", label="C_Q")
    ax_pe.plot(C_imag, "-o", label="C_I")
    ax_pe.plot(1 - A_real, "-o", label="A_Q")
    ax_pe.plot(1 - A_imag, "-o", label="A_I")
    ax_pe.plot(B_real / (B_real + 1), "-o", label="B_Q")
    ax_pe.plot(B_imag / (B_imag + 1), "-o", label="B_I")
    ax_pe.set_xlabel("Experiment number")
    ax_pe.set_ylabel("$p_e/p_g$")
    ax_pe.legend()

    print("Mean pe/pg C_real:", np.mean(C_real) * 1e2)
    print("Mean pe/pg C_imag:", np.mean(C_imag) * 1e2)
    print("Mean pe/pg A_real:", np.mean(1 - A_real) * 1e2)
    print("Mean pe/pg A_imag:", np.mean(1 - A_imag) * 1e2)
    print("Mean pe/pg B_real:", np.mean(B_real / (B_real + 1)) * 1e2)
    print("Mean pe/pg B_imag:", np.mean(B_imag / (B_imag + 1)) * 1e2)

    temperatures = {
        "T_A_real": T_calc(1 - A_real, f_q) * 1e3,
        "T_A_imag": T_calc(1 - A_imag, f_q) * 1e3,
        "T_B_real": T_calc(B_real / (B_real + 1), f_q) * 1e3,
        "T_B_imag": T_calc(B_imag / (B_imag + 1), f_q) * 1e3,
        "T_C_real": T_calc(C_real, f_q) * 1e3,
        "T_C_imag": T_calc(C_imag, f_q) * 1e3,
    }

    fig_temp, ax_temp = plt.subplots()
    ax_temp.plot(temperatures["T_A_real"], "-o", label="A_Q", color="red")
    ax_temp.plot(temperatures["T_A_imag"], "-D", mfc="w", label="A_I", color="red")
    ax_temp.plot(temperatures["T_B_real"], "-o", label="B_Q", color="blue")
    ax_temp.plot(temperatures["T_B_imag"], "-D", mfc="w", label="B_I", color="blue")
    ax_temp.plot(temperatures["T_C_real"], "-o", label="C_Q", color="green")
    ax_temp.plot(temperatures["T_C_imag"], "-D", mfc="w", label="C_I", color="green")
    ax_temp.set_xlabel("Experiment number")
    ax_temp.set_ylabel("T_eff, mK")
    ax_temp.legend()

    estimators = {"A_real": A_real, "A_imag": A_imag, "B_real": B_real, "B_imag": B_imag,
                  "C_real": C_real, "C_imag": C_imag, **temperatures}
    return fig_pe, ax_pe, fig_temp, ax_temp, estimators


def plot_prepulse_normalized_x0(pulse_amp, x0, qubit_uid: str):
    """Normalized `|x0|` vs. ge pre-pulse amplitude."""
    normalized = (np.abs(x0) - np.min(np.abs(x0))) / (np.max(np.abs(x0)) - np.min(np.abs(x0)))
    fig, ax = plt.subplots()
    ax.plot(pulse_amp, normalized, "o-")
    ax.set_xlabel("Pre-pulse amplitude, a.u.")
    ax.set_ylabel("Normalized $|x0|$")
    ax.set_title(f"Population with pre-pulse - {qubit_uid}")
    return fig, ax, normalized


def compute_and_plot_prepulse_estimator(pulse_amp, pop_prepulse_results: dict, qubit_uid: str):
    """The `A1`/`B2` pe/pg estimators (real part) vs. ge pre-pulse amplitude.

    The `x0`-derived population trace is scaled/shifted so it matches the
    residual excited population `pe0 = 1 - A1` at zero pre-pulse amplitude
    (the point where the ge pre-pulse should have no effect).

    Returns `(fig, ax, pe0)`.
    """
    proj_real = {k: v.real for k, v in pop_prepulse_results.items()}
    abc_real = get_ABC(proj_real)
    A_real, B_real = abc_real["A1"], abc_real["B2"]

    pe0 = 1 - A_real[0]
    print("Residual excited population at zero pre-pulse amplitude:", pe0)

    x0 = pop_prepulse_results["x0"]
    pe = (np.abs(x0) - np.min(np.abs(x0))) / (np.max(np.abs(x0)) - np.min(np.abs(x0)))
    pe_sh = (1 - 2 * pe0) * pe + pe0

    fig, ax = plt.subplots()
    ax.plot(pulse_amp, 1 - A_real, "-o", label="A_Q")
    ax.plot(pulse_amp, B_real / (B_real + 1), "-o", label="B_Q")
    ax.plot(pulse_amp, pe_sh / (1 - pe_sh), "-")
    ax.set_xlabel("Pre-pulse amplitude, a.u.")
    ax.set_ylabel("$p_e/p_g$")
    ax.set_ylim(0.0, 1.0)
    ax.legend()

    return fig, ax, pe0


def plot_population_vs_readout_frequency(pop_i_results: dict, readout_resonator_frequency_arr, qubit_uid: str):
    """IQ-plane and signal-distance/phase-difference plots vs. readout frequency."""
    fig_iq, ax_iq = plot_iq_projection(
        pop_i_results, ["x0", "x1"], qubit_uid,
        "Population vs. readout frequency: IQ", fmt=None,
    )

    x0, x1, y0 = pop_i_results["x0"], pop_i_results["x1"], pop_i_results["y0"]

    fig, ax = plt.subplots(2, 1, sharex=True, figsize=(10, 8))
    fig.suptitle(f"Population vs. readout frequency - {qubit_uid}")
    fig.supxlabel("Readout resonator frequency, GHz")

    ax[0].plot(readout_resonator_frequency_arr * 1e-9, np.abs(x0 - x1), "o-", label="|x0 - x1|")
    ax[0].set_ylabel("Signal distance, a.u.")
    ax[0].legend()

    ax[1].plot(
        readout_resonator_frequency_arr * 1e-9,
        np.unwrap(np.angle(x0)) - np.unwrap(np.angle(x1)), "o-", label="phase(x0) - phase(x1)",
    )
    ax[1].plot(
        readout_resonator_frequency_arr * 1e-9,
        np.unwrap(np.angle(x0)) - np.unwrap(np.angle(y0)), "o-", label="phase(x0) - phase(y0)",
    )
    ax[1].set_ylabel("Phase difference, rad")
    ax[1].legend()

    return fig_iq, ax_iq, fig, ax


def plot_temperature_vs_readout_frequency(TABC_I: dict, TABC_Q: dict, readout_resonator_frequency_arr, qubit_uid: str):
    """Every `A`/`B`/`C` estimator's I/Q temperature vs. readout frequency."""
    fig, ax = plt.subplots(1, 2, sharey=True, figsize=(12, 5))
    fig.suptitle(f"Temperature vs. readout frequency - {qubit_uid}")
    for k in TABC_I:
        ax[0].plot(readout_resonator_frequency_arr * 1e-9, TABC_I[k], label=k)
        ax[1].plot(readout_resonator_frequency_arr * 1e-9, TABC_Q[k], label=k)
    ax[0].set_title("I component")
    ax[1].set_title("Q component")
    for axis in ax:
        axis.set_xlabel("Readout resonator frequency, GHz")
        axis.set_ylim(0, 200)
        axis.legend()
    ax[0].set_ylabel("Effective temperature, mK")
    return fig, ax


def plot_temperature_iq_correlation(TABC_I: dict, TABC_Q: dict, qubit_uid: str):
    """Scatter of the I- vs. Q-component temperature of every estimator."""
    fig, ax = plt.subplots()
    ax.set_title(f"Temperature I vs. Q - {qubit_uid}")
    for k in TABC_I:
        ax.plot(TABC_I[k], TABC_Q[k], "o", label=k)
    ax.set_xlim(0, 200)
    ax.set_ylim(0, 200)
    ax.set_xlabel("T_eff (I), mK")
    ax.set_ylabel("T_eff (Q), mK")
    ax.legend()
    return fig, ax


def pick_optimal_readout_frequency(TABC_I: dict, readout_resonator_frequency_arr, skip=()):
    """The readout frequency with the smallest relative spread across estimators.

    Returns `(optimal_index, optimal_frequency, rel_err_vs_freq)`.
    """
    temperature_matrix = np.array([TABC_I[k] for k in TABC_I if k not in skip], dtype=float)
    rel_err_vs_freq = np.abs(
        np.nanstd(temperature_matrix, axis=0) / np.nanmean(temperature_matrix, axis=0)
    )
    optimal_index = int(np.nanargmin(rel_err_vs_freq))
    optimal_frequency = float(readout_resonator_frequency_arr[optimal_index])
    return optimal_index, optimal_frequency, rel_err_vs_freq
