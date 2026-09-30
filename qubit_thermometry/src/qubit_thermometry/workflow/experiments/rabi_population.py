"""Rabi Population Measurement (RPM) calibration experiment.

Sweeps the `ef` drive amplitude and measures both with and without a `ge`
pre-pulse (`main_wo`/`main_with`). The ratio of the two oscillation
amplitudes (see `qubit_thermometry.workflow.analysis.rabi_population`) gives
the residual excited-state population and thus the effective temperature.

Ported from `Workflow-v1.7.3.json` cell 303 (old
`get_rabi_population_calibration_measurement`,
`lib/helpers/meas_helper_mod.py`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from laboneq import workflow
from laboneq.simple import Experiment, SectionAlignment, SweepParameter, dsl
from laboneq.workflow.tasks import compile_experiment, run_experiment
from laboneq_applications.core import validation
from laboneq_applications.experiments.options import BaseExperimentOptions
from laboneq_applications.tasks.parameter_updating import (
    temporary_qpu,
    temporary_quantum_elements_from_qpu,
)

from qubit_thermometry.workflow.experiments.population import PopulationWorkflowOptions

if TYPE_CHECKING:
    import numpy as np
    from laboneq.dsl.quantum import QuantumParameters
    from laboneq.dsl.quantum.qpu import QPU
    from laboneq.dsl.session import Session

    from laboneq_applications.typing import QuantumElements


@workflow.task
@dsl.qubit_experiment
def create_rabi_population_experiment(
    qpu: QPU,
    qubit: QuantumElements,
    ef_amplitudes: np.ndarray,
    options: BaseExperimentOptions | None = None,
) -> Experiment:
    """Create the RPM calibration experiment (ef-amplitude sweep).

    Two sequences are measured at every swept `ef` amplitude:

    - `wo`:   `X_ef(theta)`, `X_ge`               -> handle `<uid>/result/wo`
    - `with`: `X_ge`, `X_ef(theta)`, `X_ge`        -> handle `<uid>/result/with`

    Arguments:
        qpu: The QPU consisting of the qubits and quantum operations.
        qubit: The qubit to run the experiment on.
        ef_amplitudes: The ef drive amplitudes to sweep over
            (old `theta_ef_sweep`).
        options: `BaseExperimentOptions`.

    Returns:
        experiment:
            The generated LabOne Q experiment instance to be compiled and executed.
    """
    opts = BaseExperimentOptions() if options is None else options
    qubit, ef_amplitudes = validation.validate_and_convert_single_qubit_sweeps(
        qubit, ef_amplitudes
    )

    max_measure_section_length = qpu.measure_section_length([qubit])
    qop = qpu.quantum_operations

    with dsl.acquire_loop_rt(
        count=opts.count,
        averaging_mode=opts.averaging_mode,
        acquisition_type=opts.acquisition_type,
        repetition_mode=opts.repetition_mode,
        repetition_time=opts.repetition_time,
        reset_oscillator_phase=opts.reset_oscillator_phase,
    ):
        with dsl.sweep(
            name=f"ef_amplitude_sweep_{qubit.uid}",
            parameter=SweepParameter(f"ef_amplitude_{qubit.uid}", ef_amplitudes),
        ) as ef_amplitude:
            # without ge pre-pulse
            with dsl.section(name="main_wo", alignment=SectionAlignment.RIGHT):
                with dsl.section(name="drive_wo", alignment=SectionAlignment.RIGHT):
                    sec = qop.x180(qubit, transition="ef", amplitude=ef_amplitude)
                    sec.alignment = SectionAlignment.RIGHT
                    sec = qop.x180(qubit, transition="ge")
                    sec.alignment = SectionAlignment.RIGHT
                with dsl.section(name="measure_wo", alignment=SectionAlignment.LEFT):
                    sec = qop.measure(
                        qubit, dsl.handles.result_handle(qubit.uid, suffix="wo")
                    )
                    sec.length = max_measure_section_length
                    qop.passive_reset(qubit)

            # with ge pre-pulse
            with dsl.section(name="main_with", alignment=SectionAlignment.RIGHT):
                with dsl.section(name="drive_with", alignment=SectionAlignment.RIGHT):
                    sec = qop.x180(qubit, transition="ge")
                    sec.alignment = SectionAlignment.RIGHT
                    sec = qop.x180(qubit, transition="ef", amplitude=ef_amplitude)
                    sec.alignment = SectionAlignment.RIGHT
                    sec = qop.x180(qubit, transition="ge")
                    sec.alignment = SectionAlignment.RIGHT
                with dsl.section(name="measure_with", alignment=SectionAlignment.LEFT):
                    sec = qop.measure(
                        qubit, dsl.handles.result_handle(qubit.uid, suffix="with")
                    )
                    sec.length = max_measure_section_length
                    qop.passive_reset(qubit)


@workflow.workflow(name="rabi_population")
def rabi_population_experiment_workflow(
    session: Session,
    qpu: QPU,
    qubit: QuantumElements,
    ef_amplitudes: np.ndarray,
    temporary_parameters: dict[str, QuantumParameters] | None = None,
    options: PopulationWorkflowOptions | None = None,
) -> None:
    """The Rabi-population-measurement calibration workflow.

    Arguments:
        session: The connected session to use for running the experiment.
        qpu: The QPU consisting of the qubits and quantum operations.
        qubit: The qubit to run the experiment on, passed by UID.
        ef_amplitudes: See `create_rabi_population_experiment`.
        temporary_parameters: The temporary parameters with which to update
            the quantum elements before running the experiment.
        options: `PopulationWorkflowOptions`.
    """
    temp_qpu = temporary_qpu(qpu, temporary_parameters)
    qubit = temporary_quantum_elements_from_qpu(temp_qpu, qubit)
    exp = create_rabi_population_experiment(
        temp_qpu,
        qubit,
        ef_amplitudes=ef_amplitudes,
    )
    compiled_exp = compile_experiment(session, exp)
    result = run_experiment(session, compiled_exp)
    workflow.return_(result)
