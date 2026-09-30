"""Plotting for the Dispersive Shift experiment (3-state spectroscopy/IQ/distance).

`laboneq_applications.experiments.dispersive_shift` already fits/updates the
optimal `readout_resonator_frequency`; this module ports the extra
diagnostic plots from `Workflow-v1.7.3.json` cells 217-218: amplitude/phase
spectroscopy traces per prepared state, an IQ-plane plot, and the per-state-
pair signal distances (from the `calculate_signal_differences` analysis
task), used to visually confirm the frequency with maximum state
discrimination.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from laboneq.simple import dsl

from qubit_thermometry.helper.setup import get_analysis_task_output

STATE_LABELS = {"g": "ground", "e": "first excited", "f": "second excited"}
STATE_COLORS = {"g": "b", "e": "r", "f": "g"}


def plot_dispersive_shift_results(workflow_result, qubit_to_measure, frequencies, states, get_path_to_file):
    """Spectroscopy/IQ/distance plots for a `dispersive_shift.experiment_workflow` result.

    Arguments:
        workflow_result: The result of `dispersive_shift.experiment_workflow(...).run()`.
        qubit_to_measure: The measured qubit (a `QuantumElement`).
        frequencies: The swept readout frequencies (Hz), as passed to the workflow.
        states: The basis states that were prepared, e.g. `"gef"`.
        get_path_to_file: A `helper.setup.get_path_to_file` bound to the
            notebook's `data_root_directory` (e.g. via `functools.partial`).

    Returns:
        A dict with keys `res_data` (per-state raw signal), `processed_data_dict`
        (per-state-pair `(distance, max_distance, freq_at_max)`), the three
        saved figure paths (`spec_path`, `iq_path`, `distance_path`), and the
        three `Figure` objects (`figures`).
    """
    result = workflow_result.output
    res_data = {
        state: result[dsl.handles.result_handle(qubit_to_measure.uid, suffix=state)].data
        for state in states
    }
    res_freq = frequencies

    fig, ax = plt.subplots(2, 1, sharex=True, figsize=(10, 8))
    fig.suptitle("Spectroscopy of readout resonator for the qubit states", fontsize=16)
    fig.supxlabel("Readout frequency, GHz")

    ax[0].set_title("Amplitude")
    ax[1].set_title("Phase")

    for state, data in res_data.items():
        ax[0].plot(res_freq * 1e-9, np.abs(data), STATE_COLORS[state], label=STATE_LABELS[state])
        ax[1].plot(
            res_freq * 1e-9,
            np.unwrap(np.angle(data)),
            STATE_COLORS[state],
            label=STATE_LABELS[state],
        )

    for axis, ylabel in zip(ax, ["Amplitude, a.u.", "Phase, a.u."]):
        axis.axvline(
            x=qubit_to_measure.parameters.readout_resonator_frequency * 1e-9,
            label="current readout",
        )
        axis.set_ylabel(ylabel)
        axis.legend()

    spec_path = get_path_to_file("Readout_spec_for_g_e", ".png")
    fig.savefig(spec_path, dpi=600, format="png", bbox_inches="tight")

    fig_iq, ax_iq = plt.subplots()
    ax_iq.set_title("Spectroscopy of readout resonator: IQ plane")
    for state, data in res_data.items():
        ax_iq.plot(data.real, data.imag, STATE_COLORS[state], label=STATE_LABELS[state])
    ax_iq.set_xlabel("Real part, a.u.")
    ax_iq.set_ylabel("Imaginary part, a.u.")
    ax_iq.legend()

    iq_path = get_path_to_file("Readout_spec_for_g_e_IQ", ".png")
    fig_iq.savefig(iq_path, dpi=600, format="png", bbox_inches="tight")

    processed_data_dict = get_analysis_task_output(workflow_result, "calculate_signal_differences")

    fig_dist, ax_dist = plt.subplots(figsize=(10, 5))
    ax_dist.set_title("Spectroscopy of readout resonator: state distances")
    for state_pair, (distance, max_distance, freq_at_max) in processed_data_dict.items():
        ax_dist.plot(res_freq * 1e-9, distance, label=state_pair)
        print(f"{state_pair}: max distance {max_distance:.4g} at {freq_at_max * 1e-9:.6f} GHz")

    ax_dist.axvline(
        x=qubit_to_measure.parameters.readout_resonator_frequency * 1e-9,
        ls="--",
        label="current readout",
    )
    optimal_pair = "sum" if "sum" in processed_data_dict else next(iter(processed_data_dict))
    ax_dist.axvline(
        x=processed_data_dict[optimal_pair][2] * 1e-9,
        ls="-.",
        color="k",
        label="optimal",
    )
    ax_dist.set_xlabel("Readout frequency, GHz")
    ax_dist.set_ylabel("Signal distance, a.u.")
    ax_dist.legend()

    distance_path = get_path_to_file("Readout_spec_for_g_e_distance", ".png")
    fig_dist.savefig(distance_path, dpi=600, format="png", bbox_inches="tight")

    return {
        "res_data": res_data,
        "processed_data_dict": processed_data_dict,
        "spec_path": spec_path,
        "iq_path": iq_path,
        "distance_path": distance_path,
        "figures": (fig, fig_iq, fig_dist),
    }
