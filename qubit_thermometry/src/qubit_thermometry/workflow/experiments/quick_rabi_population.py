"""Quick (two-point) Rabi Population Measurement experiment.

Only the two extreme points of the ef-Rabi oscillation are measured
(`ef` amplitude 0 and pi), repeated `repetitions` times in a single real-time
sweep, so this is much faster than the full amplitude sweep of
`qubit_thermometry.workflow.experiments.rabi_population` and is meant to be
run often to track the effective temperature over time.

Ported from `Workflow-v1.7.3.json` cell 305 (old
`get_quick_rabi_population_measurement`, `lib/helpers/meas_helper_mod.py`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
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
    from laboneq.dsl.quantum import QuantumParameters
    from laboneq.dsl.quantum.qpu import QPU
    from laboneq.dsl.session import Session

    from laboneq_applications.typing import QuantumElements

# The four sequences of the quick (two-point) RPM protocol, as lists of
# `(transition, amplitude)` pi-pulses played before the readout. `amplitude
# = None` uses the qubit's calibrated pi amplitude for that transition (i.e.
# the "max"/pi point); `amplitude = 0.0` is the "min"/zero point.
#   wo_min:   X_ef(0),  X_ge                 -> '<uid>/result/wo_min'
#   wo_max:   X_ef(pi), X_ge                 -> '<uid>/result/wo_max'
#   with_min: X_ge,     X_ge                 -> '<uid>/result/with_min'
#   with_max: X_ge, X_ef(pi), X_ge           -> '<uid>/result/with_max'
QUICK_RPM_SEQUENCES = {
    "wo_min": (("ef", 0.0), ("ge", None)),
    "wo_max": (("ef", None), ("ge", None)),
    "with_min": (("ge", None), ("ge", None)),
    "with_max": (("ge", None), ("ef", None), ("ge", None)),
}


@workflow.task
@dsl.qubit_experiment
def create_quick_rabi_population_experiment(
    qpu: QPU,
    qubit: QuantumElements,
    repetitions: int = 1,
    options: BaseExperimentOptions | None = None,
) -> Experiment:
    """Create the quick (two-point) RPM experiment.

    Arguments:
        qpu: The QPU consisting of the qubits and quantum operations.
        qubit: The qubit to run the experiment on.
        repetitions: How many times the four points are repeated
            (old `rep_count` of the `mock_sweep`).
        options: `BaseExperimentOptions`.

    Returns:
        experiment:
            The generated LabOne Q experiment instance to be compiled and executed.
    """
    opts = BaseExperimentOptions() if options is None else options
    qubit = validation.validate_and_convert_single_qubit_sweeps(qubit)

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
            name=f"repetition_sweep_{qubit.uid}",
            parameter=SweepParameter(f"repetition_{qubit.uid}", np.arange(repetitions)),
        ):
            for label, pulses in QUICK_RPM_SEQUENCES.items():
                with dsl.section(name=f"main_{label}", alignment=SectionAlignment.RIGHT):
                    with dsl.section(
                        name=f"drive_{label}", alignment=SectionAlignment.RIGHT
                    ):
                        for transition, amplitude in pulses:
                            sec = qop.x180(qubit, transition=transition, amplitude=amplitude)
                            sec.alignment = SectionAlignment.RIGHT
                    with dsl.section(
                        name=f"measure_{label}", alignment=SectionAlignment.LEFT
                    ):
                        sec = qop.measure(
                            qubit, dsl.handles.result_handle(qubit.uid, suffix=label)
                        )
                        sec.length = max_measure_section_length
                        qop.passive_reset(qubit)


@workflow.workflow(name="quick_rabi_population")
def quick_rabi_population_experiment_workflow(
    session: Session,
    qpu: QPU,
    qubit: QuantumElements,
    repetitions: int = 1,
    temporary_parameters: dict[str, QuantumParameters] | None = None,
    options: PopulationWorkflowOptions | None = None,
) -> None:
    """The quick Rabi-population-measurement workflow.

    Arguments:
        session: The connected session to use for running the experiment.
        qpu: The QPU consisting of the qubits and quantum operations.
        qubit: The qubit to run the experiment on, passed by UID.
        repetitions: See `create_quick_rabi_population_experiment`.
        temporary_parameters: The temporary parameters with which to update
            the quantum elements before running the experiment.
        options: `PopulationWorkflowOptions`.
    """
    temp_qpu = temporary_qpu(qpu, temporary_parameters)
    qubit = temporary_quantum_elements_from_qpu(temp_qpu, qubit)
    exp = create_quick_rabi_population_experiment(
        temp_qpu,
        qubit,
        repetitions=repetitions,
    )
    compiled_exp = compile_experiment(session, exp)
    result = run_experiment(session, compiled_exp)
    workflow.return_(result)
