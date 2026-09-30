"""Rabi chevron: a 2D amplitude-vs-detuning sweep built on `amplitude_rabi`.

This is not a LabOne Q pulse-sequence experiment itself (there is no
`create_experiment`/`@dsl.qubit_experiment` here). It repeatedly calls
`laboneq_applications.experiments.amplitude_rabi.experiment_workflow`, once
per detuning point, overriding the qubit's `resonance_frequency_{ge,ef}` via
`temporary_parameters`, and collects the raw acquired signal for every
amplitude/detuning point into a 2D array.

Ported from `Workflow-v1.7.3.json` cells 63-71 (g-e transition) and their
e-f mirror (cells 139-147), generalized into a single function parametrized
by `transition` instead of duplicating the sweep loop for each transition.
"""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

import numpy as np
from laboneq_applications.experiments import amplitude_rabi

from qubit_thermometry.helper.setup import logging_disabled

if TYPE_CHECKING:
    from laboneq.dsl.quantum.qpu import QPU
    from laboneq.dsl.quantum.quantum_element import QuantumElement
    from laboneq.dsl.session import Session


def run_rabi_chevron_sweep(
    session: Session,
    qpu: QPU,
    qubit: QuantumElement,
    transition: str,
    amplitudes: np.ndarray,
    detunings: np.ndarray,
    options,
    folder_store,
    logging_store,
    temporary_parameters_base,
) -> np.ndarray:
    """Run one amplitude-Rabi experiment per detuning point.

    Arguments:
        session: The connected LabOne Q session.
        qpu: The qpu consisting of the qubits and quantum operations.
        qubit: The single qubit under test (a `QuantumElement`, e.g. `qubits[0]`).
        transition: `"ge"` or `"ef"`; selects which resonance frequency and
            drive length are swept/overridden.
        amplitudes: The drive amplitudes to sweep at every detuning point
            (passed as `amplitudes=[amplitudes]` to `amplitude_rabi`).
        detunings: The frequency detunings (Hz) to sweep around the qubit's
            current `resonance_frequency_{ge,ef}`.
        options: An `amplitude_rabi.experiment_workflow.options()` instance.
            Typically `close_figures(True)` since per-point Rabi plots are
            not useful; the 2D chevron map is built separately, by
            `qubit_thermometry.workflow.analysis.rabi_chevron.plot_chevron_map`.
        folder_store: The `FolderStore` returned by `helper.setup.setup_logbook`.
        logging_store: The `LoggingStore` returned by `helper.setup.setup_logbook`.
        temporary_parameters_base: A `QuantumParameters` instance (e.g.
            `deepcopy(qubit.parameters)`) with `drive_range`,
            `readout_amplitude`, and `{ge,ef}_drive_length` already set as
            desired for the sweep; this function additionally overrides
            `resonance_frequency_{ge,ef}` per detuning point.

    Returns:
        The raw acquired signal, with shape `(len(detunings), len(amplitudes))`.
    """
    if transition == "ge":
        base_resonance_frequency = temporary_parameters_base.resonance_frequency_ge
    elif transition == "ef":
        base_resonance_frequency = temporary_parameters_base.resonance_frequency_ef
    else:
        raise ValueError("transition must be 'ge' or 'ef'")

    rabi_chevron_results = []

    with logging_disabled(folder_store, logging_store):
        for detuning in detunings:
            print(f"Measuring chevron point at detuning: {detuning * 1e-6:.3f} MHz")

            temp_pars = deepcopy(temporary_parameters_base)
            if transition == "ge":
                temp_pars.resonance_frequency_ge = base_resonance_frequency + detuning
            else:
                temp_pars.resonance_frequency_ef = base_resonance_frequency + detuning
            temporary_parameters = {qubit.uid: temp_pars}

            exp_workflow = amplitude_rabi.experiment_workflow(
                session=session,
                qpu=qpu,
                qubits=[qubit.uid],
                amplitudes=[amplitudes],
                options=options,
                temporary_parameters=temporary_parameters,
            )
            workflow_result = exp_workflow.run()

            # NOTE: adjust the accessor below if `get_data` does not match the
            # acquire handle used internally by the installed `amplitude_rabi`.
            raw_signal = workflow_result.tasks["run_experiment"].output.get_data(
                qubit.uid + "/result"
            )
            rabi_chevron_results.append(raw_signal)

    return np.array(rabi_chevron_results)
