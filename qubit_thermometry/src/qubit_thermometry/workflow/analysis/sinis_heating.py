"""Plotting/saving for SINIS heating-sweep and qubit-health-statistics results.

Reproduces the "Analysis Plots" and "Update Parameters" cells that followed
every heating-sweep/statistics run in the original notebook
(``Workflow-v1.7.3.json`` cells 486-490, 496-502, ..., 615-623), generalized
to accept the dicts returned by
`workflow.experiments.sinis_heating_sweep.run_heating_sweep` /
`run_qubit_health_statistics`.
"""

from __future__ import annotations

from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
from scipy.io import loadmat

from qubit_thermometry.helper.data_io import build_mat_payload, save_mat
from qubit_thermometry.helper.temperature import (
    get_ABC_parallel,
    get_temperature,
    pop_label_list,
)
from qubit_thermometry.helper.plotting import plot_temp_single


def plot_heating_sweep_results(
    result: dict,
    qubit,
    f_q,
    anharm,
    v_off,
    get_path_to_file,
    x_label: str = "V_Heater, corrected (mV)",
    x_scale: float = 1.0,
    teff_ylim=None,
    t1_ylim=None,
    file_prefix: str = "",
) -> dict:
    """Reproduce the "Analysis Plots" cells of one heating-sweep subsection.

    The bias axis is the offset-corrected heater bias `(Vheat_SIM - v_off)`,
    optionally divided by `x_scale` (e.g. `x_scale=0.216` to express it in
    units of the superconducting gap voltage, old `.../0.216`,
    `xlabel='V_Heater, corrected (eV/Delta)'`). This is equivalent to (but
    more robust than) the original notebook's `Vappl * 1e3 + 1.378`, which
    only reconstructed `Vheat_SIM - v_off` correctly because `V_div` was
    always `1000` -- see the PR notes for details.

    Always plots all five figures (SINIS voltage, effective temperature, T1,
    Ramsey detuning, Ramsey T2 -- each vs. heater bias) and always uses
    `errorbar` with the T1/Ramsey uncertainties, which is a superset of what
    individual original subsections did (the earliest two heating-sweep
    cells omitted the Ramsey-T2 plot and error bars entirely).

    Returns `{"figures": {...}, "ABC": ABC, "TABC": TABC}` so the caller can
    pass `ABC`/`TABC` on to `save_heating_sweep_data`.
    """
    x_data = (result["Vheat_SIM"] - v_off) / x_scale
    date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    figures = {}

    if "V_sinis" in result:
        fig, ax = plt.subplots()
        ax.plot(x_data, result["V_sinis"], "o-")
        ax.set_xlabel(x_label)
        ax.set_ylabel("V_SINIS")
        ax.set_title(f"SINIS voltage vs. heating - {qubit.uid}")
        fig.savefig(
            get_path_to_file(f"{file_prefix}SINIS_voltage_vs_heating_", ".png"),
            dpi=600,
            format="png",
            bbox_inches="tight",
        )
        figures["sinis_voltage"] = fig

    abc = get_ABC_parallel({label: result[label] for label in pop_label_list})
    tabc = get_temperature(abc, f_q, anharm, three_levels=True)
    fig, ax = plot_temp_single(tabc, xdata=x_data, xlabel=x_label)
    if teff_ylim is not None:
        ax.set_ylim(teff_ylim)
    fig.savefig(
        get_path_to_file(f"{file_prefix}Teff_vs_heater_bias_", ".png"),
        dpi=600,
        format="png",
        bbox_inches="tight",
    )
    figures["temperature"] = fig

    fig, ax = plt.subplots()
    ax.errorbar(x_data, result["T1"] * 1e6, yerr=result.get("T1_std", 0) * 1e6)
    if t1_ylim is not None:
        ax.set_ylim(t1_ylim)
    ax.set_ylabel("T1, us")
    ax.set_xlabel(x_label)
    ax.set_title(f"T1 vs. heater bias - {qubit.uid}")
    fig.savefig(
        get_path_to_file(f"{file_prefix}T1_vs_heater_bias_{date}_", ".png"),
        dpi=600,
        format="png",
        bbox_inches="tight",
    )
    figures["t1"] = fig

    fig, ax = plt.subplots()
    detuning = (result["ramsey_freq"] - qubit.parameters.resonance_frequency_ge) * 1e-6
    ax.errorbar(x_data, detuning, yerr=result.get("ramsey_freq_std", 0) * 1e-6)
    ax.set_ylabel("Detuning, MHz")
    ax.set_xlabel(x_label)
    ax.set_title(f"Ramsey detuning vs. heater bias - {qubit.uid}")
    fig.savefig(
        get_path_to_file(f"{file_prefix}detuning_vs_heater_bias_{date}_", ".png"),
        dpi=600,
        format="png",
        bbox_inches="tight",
    )
    figures["ramsey_detuning"] = fig

    fig, ax = plt.subplots()
    ax.errorbar(x_data, result["ramsey_T2"] * 1e6, yerr=result.get("ramsey_T2_std", 0) * 1e6)
    ax.set_ylabel("T2, us")
    ax.set_xlabel(x_label)
    ax.set_title(f"Ramsey T2 vs. heater bias - {qubit.uid}")
    fig.savefig(
        get_path_to_file(f"{file_prefix}T2_vs_heater_bias_{date}_", ".png"),
        dpi=600,
        format="png",
        bbox_inches="tight",
    )
    figures["ramsey_t2"] = fig

    return {"figures": figures, "ABC": abc, "TABC": tabc}


def plot_qubit_health_statistics(result: dict, qubit, f_q, anharm, get_path_to_file) -> dict:
    """Reproduce the "## Statistics" section's two analysis plots.

    Old cells 487-488: a 3-panel (T1/T2*/MXC temperature) plot vs.
    measurement number, plus a single-panel effective-temperature plot
    (vs. point number, since there is no bias axis here).

    Returns `{"figures": {...}, "ABC": ABC, "TABC": TABC}`.
    """
    fig, ax = plt.subplots(3, 1, sharex=True, figsize=(10, 10))
    fig.suptitle(f"Qubit health during statistics - {qubit.uid}")
    fig.supxlabel("Measurement number")

    ax[0].plot(result["T1"] * 1e6, "o-")
    ax[0].set_ylabel("T1, us")

    ax[1].plot(result["ramsey_T2"] * 1e6, "o-")
    ax[1].set_ylabel("T2*, us")

    ax[2].plot(result["MXC_temp"] * 1e3, "o-")
    ax[2].set_ylabel("MXC temperature, mK")

    fig.savefig(
        get_path_to_file("Statistic_qubit_health_", ".png"),
        dpi=600,
        format="png",
        bbox_inches="tight",
    )

    abc = get_ABC_parallel({label: result[label] for label in pop_label_list})
    tabc = get_temperature(abc, f_q, anharm, three_levels=True)
    fig_temp, ax_temp = plot_temp_single(tabc)
    fig_temp.savefig(
        get_path_to_file("Statistic_temperature_", ".png"),
        dpi=600,
        format="png",
        bbox_inches="tight",
    )

    return {
        "figures": {"qubit_health": fig, "temperature": fig_temp},
        "ABC": abc,
        "TABC": tabc,
    }


def save_heating_sweep_data(
    file_path: str,
    qubit,
    sample_name: str,
    qubit_name: str,
    cooldown_start_date: str,
    result: dict,
    tabc: dict | None = None,
    f_q=None,
    anharm=None,
    comment: str | None = None,
) -> str:
    """Build and save the `.mat` payload for one heating-sweep (or statistics) subsection.

    Merges `result` (as returned by `run_heating_sweep`/`run_qubit_health_statistics`)
    with `tabc` (the per-estimator effective-temperature dict, if computed by
    `plot_heating_sweep_results`/`plot_qubit_health_statistics`) plus `f_q`/`anharm`
    and the qubit's scalar parameters, matching the old per-cell
    `data.update(pop_full_results); data.update(TABC); data.update(
    {k: v for k, v in attrs.asdict(qubit.parameters).items() ...})` pattern.
    """
    data = dict(result)
    if tabc is not None:
        data.update(tabc)
    if f_q is not None:
        data["f_q"] = f_q
    if anharm is not None:
        data["anharm"] = anharm

    payload = build_mat_payload(
        qubit, sample_name, qubit_name, cooldown_start_date, data=data, comment=comment
    )
    return save_mat(file_path, payload)


def load_and_replot_temperature(
    mat_file_path: str,
    f_q,
    anharm,
    v_off: float,
    x_label: str = "V_Heater, corrected (eV/Delta)",
    x_scale: float = 0.216,
    ylim=None,
    skip=(),
):
    """Reload a saved heating-sweep `.mat` file and re-plot Teff vs. heater bias.

    Convenience replacement for the ad-hoc "#### test post analysis" cells
    near the end of the original SINIS section (cells 581-595): those
    manually reloaded a previously-saved `.mat` file with `scipy.io.loadmat`
    to re-plot its effective temperature without re-running the experiment.
    Only the temperature plot is reproduced, matching what those cells
    actually did (they never reloaded T1/Ramsey data for re-plotting).

    Returns `(fig, ax, TABC)`.
    """
    mat = loadmat(mat_file_path)
    pop_full_results = {label: mat[label].ravel() for label in pop_label_list}
    v_heat_sim = mat["Vheat_SIM"].ravel() if "Vheat_SIM" in mat else mat["Vheat_appl"].ravel() * 1e3
    x_data = (np.asarray(v_heat_sim) - v_off) / x_scale

    abc = get_ABC_parallel(pop_full_results)
    tabc = get_temperature(abc, f_q, anharm, three_levels=True)
    fig, ax = plot_temp_single(tabc, skip=skip, xdata=x_data, xlabel=x_label)
    if ylim is not None:
        ax.set_ylim(ylim)
    return fig, ax, tabc
