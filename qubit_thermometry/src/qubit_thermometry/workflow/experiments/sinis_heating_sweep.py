"""SINIS heating-sweep and qubit-health-statistics experiment runners.

Generalizes the "Statistics" and the ~8 near-identical "heating sweep"
subsections of the SINIS Calibration part of the notebook
(``Workflow-v1.7.3.json`` cells 481-623): ramp a SIM928 heater-bias voltage
through a bias array (with retry on instrument-communication errors), wait,
read the MXC temperature, run the population + T1 (`lifetime_measurement`) +
Ramsey experiments, optionally an `iq_blobs` single-shot-readout experiment
per point (saving shots incrementally), then read the SINIS thermometer
voltage on the DMM.

Both `run_heating_sweep` and `run_qubit_health_statistics` wrap their sweep
loop in `helper.setup.logging_disabled`, so callers do not need to repeat
that.
"""

from __future__ import annotations

import time
from copy import deepcopy

import numpy as np
from laboneq_applications.experiments import iq_blobs, lifetime_measurement, ramsey

from qubit_thermometry.helper.data_io import update_shots_mat
from qubit_thermometry.helper.setup import logging_disabled
from qubit_thermometry.helper.single_shot import collect_shots_from_result
from qubit_thermometry.helper.sinis_devices import ramp_voltage_with_retry
from qubit_thermometry.helper.temperature import (
    collect_population_from_result,
    pop_label_list,
)
from qubit_thermometry.workflow.experiments.population import (
    population_experiment_workflow,
)


def _run_pop_t1_ramsey_point(
    session,
    qpu,
    qubit,
    pop_options,
    t1_options,
    ramsey_options,
    t1_delays,
    ramsey_delays,
    ramsey_detuning,
    temporary_parameters,
):
    """One population + T1 + Ramsey measurement, returning `(pop_result, t1, ramsey_t2, ramsey_freq)`.

    Shared by `run_heating_sweep` and `run_qubit_health_statistics` -- the
    part of each sweep-point body that both old sections had in common.
    """
    exp_workflow_pop = population_experiment_workflow(
        session=session,
        qpu=qpu,
        qubit=qubit.uid,
        options=pop_options,
        temporary_parameters=temporary_parameters,
    )
    workflow_result_pop = exp_workflow_pop.run()
    pop_result = collect_population_from_result(workflow_result_pop.output, qubit.uid)

    exp_workflow_t1 = lifetime_measurement.experiment_workflow(
        session=session,
        qpu=qpu,
        qubits=[qubit.uid],
        delays=[t1_delays],
        options=t1_options,
        temporary_parameters=temporary_parameters,
    )
    workflow_result_t1 = exp_workflow_t1.run()
    t1_new_params = workflow_result_t1.tasks["analysis_workflow"].output["new_parameter_values"]
    t1 = t1_new_params[qubit.uid]["ge_T1"]

    exp_workflow_ramsey = ramsey.experiment_workflow(
        session=session,
        qpu=qpu,
        qubits=[qubit.uid],
        delays=[ramsey_delays],
        detunings=[ramsey_detuning],
        options=ramsey_options,
        temporary_parameters=temporary_parameters,
    )
    workflow_result_ramsey = exp_workflow_ramsey.run()
    ramsey_new_params = workflow_result_ramsey.tasks["analysis_workflow"].output["new_parameter_values"]
    ramsey_t2 = ramsey_new_params[qubit.uid]["ge_T2_star"]
    ramsey_freq = ramsey_new_params[qubit.uid]["resonance_frequency_ge"]

    return pop_result, t1, ramsey_t2, ramsey_freq


def _ufloat_arrays(values) -> tuple[np.ndarray, np.ndarray]:
    """Split an array of `uncertainties.ufloat`s into `(nominal_values, std_devs)`."""
    arr = np.array(values)
    return (
        np.array([x.nominal_value for x in arr]),
        np.array([x.std_dev for x in arr]),
    )


def run_heating_sweep(
    session,
    qpu,
    qubit,
    bias_array,
    sim,
    dmm,
    bft_controller,
    v_off,
    v_div,
    pop_options,
    t1_options,
    ramsey_options,
    t1_delays,
    ramsey_delays,
    ramsey_detuning,
    folder_store,
    logging_store,
    wait_time=5,
    n_ramp_steps=20,
    ramp_back_n_steps=100,
    ramp_back_to_off=True,
    read_mxc_temperature=True,
    mock_mxc_temperature=11.0,
    include_ssro=False,
    ssro_options=None,
    ssro_states="gef",
    shots_file_paths=None,
) -> dict:
    """Sweep `sim`'s bias through `bias_array`, measuring population/T1/Ramsey (+ optional SSRO) at each point.

    Arguments:
        session: The connected LabOne Q `Session`.
        qpu: The QPU (qubits + quantum operations).
        qubit: The `TunableTransmonQubit` to measure (old `qubit_to_measure`).
        bias_array: SIM output voltages to sweep through, in order (old
            `VSIM`).
        sim: The `SIM928` heater-bias voltage source to ramp (SINIS A ->
            `sim`, SINIS C -> `sim2`; see `helper.sinis_devices.connect_sim_voltage_source`).
        dmm: The `KeysightDMM34465A` used to read the SINIS thermometer
            voltage after each point, or `None` to skip that read.
        bft_controller: The `BlueFTController` used to read the MXC
            temperature (see `read_mxc_temperature`).
        v_off: The heater's nominal "off" bias (old `V_off`), used both as
            the ramp-back target and to compute the offset-corrected bias
            axis for plotting (`workflow.analysis.sinis_heating.plot_heating_sweep_results`).
        v_div: The external voltage divider ratio between `sim`'s output and
            the voltage actually applied to the heater; only used to compute
            the informational `Vheat_appl` array in the returned dict (old
            `Vappl_list.append(V_set / V_div)`), not for the plotted axis.
        pop_options, t1_options, ramsey_options: `.options()` of
            `population_experiment_workflow`, `lifetime_measurement.experiment_workflow`
            and `ramsey.experiment_workflow`, pre-configured by the caller.
        t1_delays, ramsey_delays, ramsey_detuning: Sweep arrays/value passed
            straight through to the T1 and Ramsey workflows.
        folder_store, logging_store: From `helper.setup.setup_logbook`; the
            whole sweep loop is wrapped in `helper.setup.logging_disabled`.
        wait_time: Seconds to wait after ramping before measuring, and
            between ramp retries (old `wait_time_2`).
        n_ramp_steps: `N_steps` passed to `sim.ramp(...)` for each sweep
            point (old cells used `20` for the two early "nonlocal, low/high
            bias" sweeps and `100` for every "local"/SSRO sweep afterwards --
            keep this per-call, do not hardcode one value).
        ramp_back_n_steps: `N_steps` used for the final ramp back to `v_off`
            once the sweep finishes (`100` in every original subsection).
        ramp_back_to_off: If True (default), ramp `sim` back to `v_off`
            (with retry) after the sweep completes.
        read_mxc_temperature: If True (default), read `bft_controller`'s MXC
            temperature at every point. The original "Short"/"Long -- Local
            Heating ... Split geometry" cells (no SSRO) had the real read
            commented out and appended a hardcoded placeholder instead --
            pass `read_mxc_temperature=False` to reproduce that (see
            `mock_mxc_temperature` and the PR notes for a caveat about the
            exact original placeholder value).
        mock_mxc_temperature: Value appended to the temperature array when
            `read_mxc_temperature=False`.
        include_ssro: If True, also run an `iq_blobs.experiment_workflow` at
            every point and append its shots to `shots_file_paths` via
            `helper.data_io.update_shots_mat` (old "... With SSRO"
            subsections).
        ssro_options: `iq_blobs.experiment_workflow.options()`, required if
            `include_ssro=True`.
        ssro_states: States string/tuple passed to `iq_blobs` and
            `collect_shots_from_result` (old `states=('gef')`, i.e. the
            plain string `"gef"`).
        shots_file_paths: `{"g": path, "e": path, "f": path}` `.mat` file
            paths to incrementally append shots to, required if
            `include_ssro=True`.

    Returns:
        A dict of arrays (one entry per bias point, plus the six population
        traces under their `x0`/`x1`/.../`y2` keys) suitable for passing to
        `workflow.analysis.sinis_heating.plot_heating_sweep_results` and
        `save_heating_sweep_data`.
    """
    if include_ssro and (ssro_options is None or shots_file_paths is None):
        raise ValueError(
            "`ssro_options` and `shots_file_paths` are required when `include_ssro=True`."
        )

    temporary_parameters = {qubit.uid: deepcopy(qubit.parameters)}

    pop_full_results: dict[str, list] = {}
    t1_list = []
    ramsey_t2_list = []
    ramsey_freq_list = []
    temp_info_list = []
    dmm_list = []
    timestamp = []
    v_appl_list = []

    with logging_disabled(folder_store, logging_store):
        for i, v_set in enumerate(bias_array):
            print("Point", i + 1, "out of", len(bias_array))
            print("Voltage on SIM:", v_set)

            ramp_voltage_with_retry(sim, v_set, n_steps=n_ramp_steps, wait_time=wait_time)
            time.sleep(wait_time)

            timestamp.append(time.time())
            v_appl_list.append(v_set / v_div)

            if read_mxc_temperature:
                response = bft_controller.get_mxc_temperature()
                temp_info_list.append(response)
                print("MXC temperature:", response * 1e3, "mK")
            else:
                temp_info_list.append(mock_mxc_temperature)

            pop_result, t1, ramsey_t2, ramsey_freq = _run_pop_t1_ramsey_point(
                session,
                qpu,
                qubit,
                pop_options,
                t1_options,
                ramsey_options,
                t1_delays,
                ramsey_delays,
                ramsey_detuning,
                temporary_parameters,
            )
            for label in pop_label_list:
                pop_full_results.setdefault(label, []).append(pop_result[label])
            t1_list.append(t1)
            ramsey_t2_list.append(ramsey_t2)
            ramsey_freq_list.append(ramsey_freq)

            if include_ssro:
                exp_workflow_ssro = iq_blobs.experiment_workflow(
                    session=session,
                    qpu=qpu,
                    qubits=[qubit.uid],
                    states=ssro_states,
                    options=ssro_options,
                    temporary_parameters=temporary_parameters,
                )
                workflow_result_ssro = exp_workflow_ssro.run()
                shots_per_state = collect_shots_from_result(
                    workflow_result_ssro.output, qubit.uid, ssro_states
                )
                for state, file_path in shots_file_paths.items():
                    update_shots_mat(file_path, shots_per_state[state])

            if dmm is not None:
                v_meas = dmm.scan()
                dmm_list.append(float(v_meas))
                print("Measured voltage:", v_meas)

        if ramp_back_to_off:
            ramp_voltage_with_retry(sim, v_off, n_steps=ramp_back_n_steps, wait_time=wait_time)

    for label in pop_label_list:
        pop_full_results[label] = np.array(pop_full_results[label])

    t1_values, t1_std = _ufloat_arrays(t1_list)
    ramsey_t2_values, ramsey_t2_std = _ufloat_arrays(ramsey_t2_list)
    ramsey_freq_values, ramsey_freq_std = _ufloat_arrays(ramsey_freq_list)

    result = {
        "timestamp": np.array(timestamp),
        "MXC_temp": np.array(temp_info_list),
        "Vheat_appl": np.array(v_appl_list),
        "Vheat_SIM": np.asarray(bias_array),
        "T1": t1_values,
        "T1_std": t1_std,
        "t1_delays": t1_delays,
        "ramsey_T2": ramsey_t2_values,
        "ramsey_T2_std": ramsey_t2_std,
        "ramsey_freq": ramsey_freq_values,
        "ramsey_freq_std": ramsey_freq_std,
        "ramsey_delays": ramsey_delays,
        "ramsey_detuning": ramsey_detuning,
    }
    if dmm is not None:
        result["V_sinis"] = np.array(dmm_list)
    result.update(pop_full_results)
    return result


def run_qubit_health_statistics(
    session,
    qpu,
    qubit,
    n_measurements,
    bft_controller,
    pop_options,
    t1_options,
    ramsey_options,
    t1_delays,
    ramsey_delays,
    ramsey_detuning,
    folder_store,
    logging_store,
) -> dict:
    """Repeat population + T1 + Ramsey `n_measurements` times without changing any bias.

    Old "## Statistics" section (cells 481-490): tracks qubit health (T1,
    T2*, MXC temperature) over time to characterize measurement-to-measurement
    variability, with no SIM ramp and no DMM read. Kept as its own function
    (rather than `run_heating_sweep(bias_array=None, ...)`) since it has no
    bias/ramp/DMM concept at all.
    """
    temporary_parameters = {qubit.uid: deepcopy(qubit.parameters)}

    pop_full_results: dict[str, list] = {}
    t1_list = []
    ramsey_t2_list = []
    ramsey_freq_list = []
    temp_info_list = []
    timestamp = []

    with logging_disabled(folder_store, logging_store):
        for i in range(n_measurements):
            print("Measurement number:", i)

            timestamp.append(time.time())

            response = bft_controller.get_mxc_temperature()
            temp_info_list.append(response)
            print("MXC temperature:", response * 1e3, "mK")

            pop_result, t1, ramsey_t2, ramsey_freq = _run_pop_t1_ramsey_point(
                session,
                qpu,
                qubit,
                pop_options,
                t1_options,
                ramsey_options,
                t1_delays,
                ramsey_delays,
                ramsey_detuning,
                temporary_parameters,
            )
            for label in pop_label_list:
                pop_full_results.setdefault(label, []).append(pop_result[label])
            t1_list.append(t1)
            ramsey_t2_list.append(ramsey_t2)
            ramsey_freq_list.append(ramsey_freq)

    for label in pop_label_list:
        pop_full_results[label] = np.array(pop_full_results[label])

    t1_values, t1_std = _ufloat_arrays(t1_list)
    ramsey_t2_values, ramsey_t2_std = _ufloat_arrays(ramsey_t2_list)
    ramsey_freq_values, ramsey_freq_std = _ufloat_arrays(ramsey_freq_list)

    result = {
        "timestamp": np.array(timestamp),
        "MXC_temp": np.array(temp_info_list),
        "T1": t1_values,
        "T1_std": t1_std,
        "t1_delays": t1_delays,
        "ramsey_T2": ramsey_t2_values,
        "ramsey_T2_std": ramsey_t2_std,
        "ramsey_freq": ramsey_freq_values,
        "ramsey_freq_std": ramsey_freq_std,
        "ramsey_delays": ramsey_delays,
        "ramsey_detuning": ramsey_detuning,
        "n_measurements": n_measurements,
    }
    result.update(pop_full_results)
    return result
