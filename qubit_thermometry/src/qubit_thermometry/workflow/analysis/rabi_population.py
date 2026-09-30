"""Rabi Population Measurement (RPM) analysis: fits and plots.

Pairs with `qubit_thermometry.workflow.experiments.rabi_population`
(full ef-amplitude sweep, used to calibrate the ef pi-pulse for the fast
two-point version) and `...experiments.quick_rabi_population` (the
fast/repeated two-point measurement used to track the effective temperature
over time).

Uses `qubit_thermometry.helper.fitting.func_osc`/`fit_rabi_osc`/
`normalize_1d_osc` for the oscillation fits and
`qubit_thermometry.helper.temperature.qrpm_dict_from_results`/`T_calc` for
the pe/pg -> temperature conversion.

Ported from `Workflow-v1.7.3.json` cells 314-316 (full RPM oscillations),
319 (pi-pulse check), 328-331 (quick RPM) and 334 (quick RPM temperature).
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from laboneq.simple import dsl

from qubit_thermometry.helper.fitting import fit_rabi_osc, func_osc, normalize_1d_osc


def collect_rpm_traces(result, qubit_uid: str, ef_amplitudes) -> dict:
    """The `with`/`wo` magnitude and (unwrapped) phase traces of a full RPM sweep."""
    rpm_res = {}
    for pre_pulse in ["with", "wo"]:
        data = result[dsl.handles.result_handle(qubit_uid, suffix=pre_pulse)].data
        rpm_res[pre_pulse] = {
            "amp": ef_amplitudes,
            "mag": np.abs(data),
            "pha": np.unwrap(np.angle(data)),
        }
    return rpm_res


def fit_rpm_oscillations(rpm_res: dict, freq_estimate: float = 8) -> tuple[dict, dict]:
    """Fit `func_osc` to the magnitude and phase traces of both `with`/`wo` sequences."""
    rpm_popt: dict = {"with": {}, "wo": {}}
    rpm_pcov: dict = {"with": {}, "wo": {}}

    for pre_pulse in ["with", "wo"]:
        rpm_popt[pre_pulse]["mag"], rpm_pcov[pre_pulse]["mag"] = fit_rabi_osc(
            x=rpm_res[pre_pulse]["amp"], y=rpm_res[pre_pulse]["mag"],
            freq=freq_estimate, phase=1.0, amp=1.0, off=0.018, plot=False,
        )
        rpm_popt[pre_pulse]["pha"], rpm_pcov[pre_pulse]["pha"] = fit_rabi_osc(
            x=rpm_res[pre_pulse]["amp"], y=rpm_res[pre_pulse]["pha"],
            freq=freq_estimate, phase=1.0, amp=0.01, off=-0.12, plot=False,
        )
    return rpm_popt, rpm_pcov


def plot_rpm_oscillations(rpm_res: dict, rpm_popt: dict, qubit_uid: str, n_points_multiplier: int = 20):
    """The 6-panel raw + fitted + normalized magnitude/phase oscillation plot.

    Returns `(fig, axs, amp_plot)`; `amp_plot` is the fine amplitude grid used
    for the fitted curves, reused by `plot_pi_pulse_check`.
    """
    amp_plot = np.linspace(
        rpm_res["with"]["amp"][0], rpm_res["with"]["amp"][-1],
        int(rpm_res["with"]["amp"].shape[0] * n_points_multiplier),
    )

    fig, axs = plt.subplots(6, 1, figsize=(10, 18), sharex=True)
    fig.suptitle(f"Rabi population measurement - {qubit_uid}")

    axs[0].scatter(rpm_res["with"]["amp"], rpm_res["with"]["mag"])
    axs[0].set_ylabel("Amplitude with pre-pulse")
    axs[0].plot(amp_plot, func_osc(amp_plot, *rpm_popt["with"]["mag"]), color="tab:red", linestyle="dashed")

    axs[1].scatter(rpm_res["wo"]["amp"], rpm_res["wo"]["mag"])
    axs[1].set_ylabel("Amplitude without pre-pulse")
    axs[1].plot(amp_plot, func_osc(amp_plot, *rpm_popt["wo"]["mag"]), color="tab:red", linestyle="dashed")

    axs[2].scatter(rpm_res["with"]["amp"], rpm_res["with"]["pha"])
    axs[2].set_ylabel("Phase with pre-pulse")
    axs[2].plot(amp_plot, func_osc(amp_plot, *rpm_popt["with"]["pha"]), color="tab:red", linestyle="dashed")

    axs[3].scatter(rpm_res["wo"]["amp"], rpm_res["wo"]["pha"])
    axs[3].set_ylabel("Phase without pre-pulse")
    axs[3].plot(amp_plot, func_osc(amp_plot, *rpm_popt["wo"]["pha"]), color="tab:red", linestyle="dashed")

    _, offset, norm = normalize_1d_osc(rpm_res["with"]["mag"])
    axs[4].scatter(rpm_res["with"]["amp"], normalize_1d_osc(rpm_res["with"]["mag"])[0], label="with", color="salmon")
    axs[4].plot(
        amp_plot, normalize_1d_osc(func_osc(amp_plot, *rpm_popt["with"]["mag"]), offset, norm)[0],
        color="tab:red", linestyle="dashed",
    )
    axs[4].scatter(rpm_res["wo"]["amp"], normalize_1d_osc(rpm_res["wo"]["mag"], norm=norm)[0], label="w/o", color="skyblue")
    axs[4].set_ylabel("Amplitude (normalized)")
    axs[4].plot(
        amp_plot, normalize_1d_osc(func_osc(amp_plot, *rpm_popt["wo"]["mag"]), norm=norm)[0],
        color="tab:blue", linestyle="dashed",
    )
    axs[4].legend()

    _, offset, norm = normalize_1d_osc(rpm_res["with"]["pha"])
    axs[5].scatter(rpm_res["with"]["amp"], normalize_1d_osc(rpm_res["with"]["pha"])[0], label="with", color="salmon")
    axs[5].plot(
        amp_plot, normalize_1d_osc(func_osc(amp_plot, *rpm_popt["with"]["pha"]), offset, norm)[0],
        color="tab:red", linestyle="dashed",
    )
    axs[5].scatter(rpm_res["wo"]["amp"], normalize_1d_osc(rpm_res["wo"]["pha"], norm=norm)[0], label="w/o", color="skyblue")
    axs[5].set_ylabel("Phase (normalized)")
    axs[5].plot(
        amp_plot, normalize_1d_osc(func_osc(amp_plot, *rpm_popt["wo"]["pha"]), norm=norm)[0],
        color="tab:blue", linestyle="dashed",
    )
    axs[5].legend()

    axs[-1].set_xlabel("ef-amplitude")
    return fig, axs, amp_plot


def plot_pi_pulse_check(
    rpm_res: dict, rpm_popt: dict, amp_plot, amp_with: float, amp_wo: float,
    qubit_uid: str, signal_in_mag: bool = True,
):
    """The RPM ef pi-pulse calibration plot: fitted oscillation + candidate pi amplitudes."""
    key = "mag" if signal_in_mag else "pha"
    ylabel = "Amplitude" if signal_in_mag else "Phase"
    fit_params_with = rpm_popt["with"][key]
    fit_params_wo = rpm_popt["wo"][key]
    with_dat = rpm_res["with"][key]
    wo_dat = rpm_res["wo"][key]

    amp_avg = (amp_with + amp_wo) / 2

    fig, axs = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    fig.suptitle(f"RPM ef pi-pulse calibration - {qubit_uid}")

    axs[0].scatter(rpm_res["wo"]["amp"], with_dat)
    axs[0].plot(amp_plot, func_osc(amp_plot, *fit_params_with), color="tab:red", linestyle="dashed")
    axs[0].vlines([amp_with], with_dat.min(), with_dat.max(), color="black", linestyle="dashed", label="with")
    axs[0].vlines([amp_avg], with_dat.min(), with_dat.max(), color="tab:green", linestyle="dashed", label="avg")
    axs[0].vlines([amp_wo], with_dat.min(), with_dat.max(), color="tab:purple", linestyle="dashed", label="wo")
    axs[0].legend()
    axs[0].set_ylabel(ylabel)
    axs[0].set_title("with ge pre pulse")

    axs[1].scatter(rpm_res["wo"]["amp"], wo_dat)
    axs[1].plot(amp_plot, func_osc(amp_plot, *fit_params_wo), color="tab:red", linestyle="dashed")
    axs[1].vlines([amp_with], wo_dat.min(), wo_dat.max(), color="black", linestyle="dashed", label="with")
    axs[1].vlines([amp_avg], wo_dat.min(), wo_dat.max(), color="tab:green", linestyle="dashed", label="avg")
    axs[1].vlines([amp_wo], wo_dat.min(), wo_dat.max(), color="tab:purple", linestyle="dashed", label="wo")
    axs[1].legend()
    axs[1].set_xlabel("ef amplitude")
    axs[1].set_ylabel(ylabel)
    axs[1].set_title("without ge pre pulse")

    return fig, axs, amp_avg


def collect_quick_rpm_traces(result, qubit_uid: str) -> dict:
    """The `with`/`wo` min/max magnitude, phase and I/Q traces of a quick RPM measurement."""
    rpm_res = {}
    for pre_pulse in ["with", "wo"]:
        data = {
            point: result[
                dsl.handles.result_handle(qubit_uid, suffix=f"{pre_pulse}_{point}")
            ].data
            for point in ["min", "max"]
        }
        rpm_res[pre_pulse] = {
            "mag_min": np.abs(data["min"]),
            "pha_min": np.angle(data["min"]),
            "mag_max": np.abs(data["max"]),
            "pha_max": np.angle(data["max"]),
            "I_max": np.real(data["max"]),
            "Q_max": np.imag(data["max"]),
            "I_min": np.real(data["min"]),
            "Q_min": np.imag(data["min"]),
        }
    return rpm_res


def plot_quick_rpm_iq(rpm_res: dict, qubit_uid: str):
    """IQ scatter of the quick RPM min/max points, with and without pre-pulse."""
    fig, axs = plt.subplots(2, 1, figsize=(10, 12))

    axs[0].scatter(rpm_res["with"]["I_max"], rpm_res["with"]["Q_max"])
    axs[0].scatter(rpm_res["with"]["I_min"], rpm_res["with"]["Q_min"])
    axs[0].set_xlabel("I")
    axs[0].set_ylabel("Q")
    axs[0].set_title("Quick RPM with ge pre-pulse")

    axs[1].scatter(rpm_res["wo"]["I_max"], rpm_res["wo"]["Q_max"])
    axs[1].scatter(rpm_res["wo"]["I_min"], rpm_res["wo"]["Q_min"])
    axs[1].set_xlabel("I")
    axs[1].set_ylabel("Q")
    axs[1].set_title("Quick RPM without ge pre-pulse")

    return fig, axs


def plot_quick_rpm_points(
    rpm_res: dict, rpm_popt: dict, amp_plot, ef_drive_amplitude_pi_rpm: float, qubit_uid: str,
):
    """Quick RPM min/max points overlaid on the full-sweep oscillation fits."""
    fig, axs = plt.subplots(4, 1, figsize=(10, 12), sharex=True)
    fig.suptitle(f"Quick RPM - {qubit_uid}")

    y_min = np.repeat(0, rpm_res["with"]["mag_min"].size)
    y_max = np.repeat(ef_drive_amplitude_pi_rpm, rpm_res["with"]["mag_min"].size)

    for axis, pre_pulse, key in zip(
        axs, ["with", "wo", "with", "wo"], ["mag", "mag", "pha", "pha"], strict=False,
    ):
        axis.scatter(y_min, rpm_res[pre_pulse][f"{key}_min"])
        axis.scatter(y_max, rpm_res[pre_pulse][f"{key}_max"])
        axis.scatter(np.mean(y_min), np.mean(rpm_res[pre_pulse][f"{key}_min"]), marker="x", color="black", s=200)
        axis.scatter(np.mean(y_max), np.mean(rpm_res[pre_pulse][f"{key}_max"]), marker="x", color="black", s=200)
        axis.plot(amp_plot, func_osc(amp_plot, *rpm_popt[pre_pulse][key]), color="tab:red", linestyle="dashed")

    for axis, ylabel, title in zip(
        axs,
        ["Amplitude", "Amplitude", "Phase", "Phase"],
        ["with ge pre-pulse", "without ge pre-pulse", "with ge pre-pulse", "without ge pre-pulse"],
        strict=False,
    ):
        axis.set_ylabel(ylabel)
        axis.set_title(title)

    axs[-1].set_xlabel("ef amplitude")
    return fig, axs


def compute_iq_pulse_distances(rpm_res: dict) -> tuple[np.ndarray, np.ndarray]:
    """Euclidean IQ distance between the min/max points, for `with`/`wo` pre-pulse."""
    max_iq_with = np.column_stack((rpm_res["with"]["I_max"], rpm_res["with"]["Q_max"]))
    min_iq_with = np.column_stack((rpm_res["with"]["I_min"], rpm_res["with"]["Q_min"]))
    iq_amp_with = np.linalg.norm(max_iq_with - min_iq_with, axis=1)

    max_iq_wo = np.column_stack((rpm_res["wo"]["I_max"], rpm_res["wo"]["Q_max"]))
    min_iq_wo = np.column_stack((rpm_res["wo"]["I_min"], rpm_res["wo"]["Q_min"]))
    iq_amp_wo = np.linalg.norm(max_iq_wo - min_iq_wo, axis=1)

    return iq_amp_with, iq_amp_wo


def plot_iq_pulse_distances(iq_amp_with, iq_amp_wo, qubit_uid: str):
    """IQ distance vs. measurement number, with and without pre-pulse."""
    fig, axs = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle(f"Quick RPM IQ distances - {qubit_uid}")
    axs[0].plot(iq_amp_with, marker="o")
    axs[0].set_ylabel("with pre-pulse")
    axs[1].plot(iq_amp_wo, marker="o")
    axs[1].set_ylabel("without pre-pulse")
    axs[1].set_xlabel("Measurement")
    return fig, axs


def plot_rpm_temperature(rpm_pe, rpm_temp, qubit_uid: str):
    """Effective-temperature series and histogram from a quick-RPM `pe`/temperature trace."""
    fig_series, ax_series = plt.subplots(figsize=(15, 5))
    ax_series.plot(np.arange(len(rpm_pe)), rpm_temp, marker="o")
    ax_series.hlines([np.mean(rpm_temp)], 0, len(rpm_pe), color="black", linestyle="dashed", label="average")
    ax_series.set_ylabel("temp (K)")
    ax_series.set_xlabel("Measurement")
    ax_series.set_title(f"Quick Rabi Population Measurement - {qubit_uid}")
    ax_series.legend()

    fig_hist, ax_hist = plt.subplots()
    ax_hist.hist(rpm_temp, bins=75)
    ax_hist.set_xlabel("Temperature")
    ax_hist.set_ylabel("Counts")
    ax_hist.set_title(f"Quick Rabi Population Measurement - {qubit_uid}")

    print("Mean pe:          ", np.mean(rpm_pe))
    print("Mean temperature: ", np.mean(rpm_temp) * 1e3, "mK")

    return fig_series, ax_series, fig_hist, ax_hist
