"""Rabi frequency calibration: pi-pulse amplitude vs. drive-pulse-length sweep.

Not a LabOne Q pulse-sequence experiment itself. Repeatedly calls
`laboneq_applications.experiments.amplitude_rabi.experiment_workflow`, once
per drive length, fixing `{ge,ef}_drive_length` via `temporary_parameters`
and reading back the fitted pi-pulse amplitude from each run's
`analysis_workflow` output.

Ported from `Workflow-v1.7.3.json` cells 72-80 (g-e transition) and their
e-f mirror (cells 148-156), generalized into a single function parametrized
by `transition` instead of duplicating the sweep loop for each transition.
The linear fit + plot of amplitude vs. 1/length lives in
`qubit_thermometry.workflow.analysis.rabi_frequency_calibration`.
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


def run_rabi_frequency_calibration_sweep(
    session: Session,
    qpu: QPU,
    qubit: QuantumElement,
    transition: str,
    amplitudes: np.ndarray,
    drive_lengths: np.ndarray,
    options,
    folder_store,
    logging_store,
    temporary_parameters_base,
) -> np.ndarray:
    """Run one amplitude-Rabi experiment per drive length; return fitted pi-amplitudes.

    Arguments:
        session: The connected LabOne Q session.
        qpu: The qpu consisting of the qubits and quantum operations.
        qubit: The single qubit under test (a `QuantumElement`, e.g. `qubits[0]`).
        transition: `"ge"` or `"ef"`; selects which drive length is
            overridden and which fitted pi-amplitude key is read back.
        amplitudes: The drive amplitudes to sweep at every drive-length point
            (passed as `amplitudes=[amplitudes]` to `amplitude_rabi`).
        drive_lengths: The drive-pulse lengths (s) to sweep.
        options: An `amplitude_rabi.experiment_workflow.options()` instance.
            Typically `close_figures(True)` since per-point Rabi plots are
            not useful; the amplitude-vs-1/length fit+plot is built
            separately, by
            `qubit_thermometry.workflow.analysis.rabi_frequency_calibration.fit_and_plot_rabi_frequency_calibration`.
        folder_store: The `FolderStore` returned by `helper.setup.setup_logbook`.
        logging_store: The `LoggingStore` returned by `helper.setup.setup_logbook`.
        temporary_parameters_base: A `QuantumParameters` instance (e.g.
            `deepcopy(qubit.parameters)`) with `drive_range`/
            `readout_amplitude` already set as desired for the sweep; this
            function additionally overrides `{ge,ef}_drive_length` per
            sweep point.

    Returns:
        An array of fitted pi-pulse amplitudes, one per drive length.
    """
    if transition not in ("ge", "ef"):
        raise ValueError("transition must be 'ge' or 'ef'")

    fitted_pi_amplitudes = []

    with logging_disabled(folder_store, logging_store):
        for drive_length in drive_lengths:
            print(f"Measuring Rabi with drive length: {drive_length * 1e9:.1f} ns")

            temp_pars = deepcopy(temporary_parameters_base)
            if transition == "ge":
                temp_pars.ge_drive_length = drive_length
            else:
                temp_pars.ef_drive_length = drive_length
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

            analysis_workflow_result = workflow_result.tasks["analysis_workflow"]
            # NOTE: adjust the key names below to match the installed library
            # version if `new_parameter_values` is not nested exactly this way.
            new_parameter_values = analysis_workflow_result.output["new_parameter_values"]
            if transition == "ge":
                fitted_pi_amplitude = new_parameter_values[qubit.uid]["ge_drive_amplitude_pi"]
            else:
                fitted_pi_amplitude = new_parameter_values[qubit.uid]["ef_drive_amplitude_pi"]
            fitted_pi_amplitudes.append(fitted_pi_amplitude)

    return np.array(fitted_pi_amplitudes)
