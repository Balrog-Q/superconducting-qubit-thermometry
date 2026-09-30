"""Three-level population experiment (the six-sequence protocol).

`laboneq_applications` has no population-measurement experiment, so this
module defines one in the same `create_*_experiment`
(`@workflow.task`/`@dsl.qubit_experiment`) + `*_experiment_workflow`
(`@workflow.workflow`) style used throughout `laboneq_applications.experiments`
(see e.g. `amplitude_rabi.py`).

Six sequences of `ge`/`ef` pi-pulses are played before the readout
(`x0`, `x1`, `x2`, `y0`, `y1`, `y2`); their acquired signals feed the
`pe/pg`/effective-temperature estimators in
:mod:`qubit_thermometry.helper.temperature`. Optionally, a `ge` drive pulse
of swept amplitude is played in front of every sequence (`prepulse_amplitudes`)
to map out the residual excited-state population vs. pre-pulse amplitude.

`PopulationWorkflowOptions` is the shared (empty) workflow-options class used
by all three custom population workflows (`population`, `rabi_population`,
`quick_rabi_population`); it is defined once here and imported by
`rabi_population.py`/`quick_rabi_population.py`.

Ported from `Workflow-v1.7.3.json` cells 298-301 (old
`make_exp_population_full`/`make_exp_population_prepulse` in
`lib/helpers/meas_helper_mod.py` + `create_exp_population_full` in
`lib/helpers/create_meas_helper.py`).
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

if TYPE_CHECKING:
    import numpy as np
    from laboneq.dsl.quantum import QuantumParameters
    from laboneq.dsl.quantum.qpu import QPU
    from laboneq.dsl.session import Session

    from laboneq_applications.typing import QuantumElements

# The six sequences of the three-level protocol, as lists of pi-pulse
# transitions played before the readout:
#   x0: -                 (thermal state)
#   x1: X_ge
#   x2: X_ge, X_ef
#   y0: X_ef
#   y1: X_ef, X_ge
#   y2: X_ef, X_ge, X_ef
POPULATION_SEQUENCES = {
    "x0": (),
    "x1": ("ge",),
    "x2": ("ge", "ef"),
    "y0": ("ef",),
    "y1": ("ef", "ge"),
    "y2": ("ef", "ge", "ef"),
}


@workflow.workflow_options
class PopulationWorkflowOptions:
    """Options shared by the `population`/`rabi_population`/`quick_rabi_population` workflows.

    There is no analysis workflow for these experiments, so only the options
    of the `create_experiment` task (`count`, `averaging_mode`, ...) are
    relevant.
    """


@workflow.task
@dsl.qubit_experiment
def create_population_experiment(
    qpu: QPU,
    qubit: QuantumElements,
    prepulse_amplitudes: np.ndarray | None = None,
    options: BaseExperimentOptions | None = None,
) -> Experiment:
    """Create the three-level population experiment.

    Arguments:
        qpu: The QPU consisting of the qubits and quantum operations.
        qubit: The qubit to run the experiment on.
        prepulse_amplitudes: If not None, a `ge` drive pulse with these
            amplitudes is played in front of every sequence and swept in
            real time (old `make_exp_population_prepulse`). If None, the
            plain six-sequence experiment is created (old
            `make_exp_population_full`).
        options: `BaseExperimentOptions`. The defaults (`AveragingMode.CYCLIC`,
            `AcquisitionType.INTEGRATION`) are what the old experiment used.

    Returns:
        experiment:
            The generated LabOne Q experiment instance to be compiled and executed.
    """
    opts = BaseExperimentOptions() if options is None else options
    if prepulse_amplitudes is None:
        qubit = validation.validate_and_convert_single_qubit_sweeps(qubit)
    else:
        qubit, prepulse_amplitudes = validation.validate_and_convert_single_qubit_sweeps(
            qubit, prepulse_amplitudes
        )

    max_measure_section_length = qpu.measure_section_length([qubit])
    qop = qpu.quantum_operations

    def _sequences(prepulse_amplitude=None):
        for label, transitions in POPULATION_SEQUENCES.items():
            with dsl.section(name=f"main_{label}", alignment=SectionAlignment.RIGHT):
                if prepulse_amplitude is not None or transitions:
                    with dsl.section(
                        name=f"drive_{label}", alignment=SectionAlignment.RIGHT
                    ):
                        if prepulse_amplitude is not None:
                            sec = qop.x180(
                                qubit, transition="ge", amplitude=prepulse_amplitude
                            )
                            sec.alignment = SectionAlignment.RIGHT
                        for transition in transitions:
                            sec = qop.x180(qubit, transition=transition)
                            sec.alignment = SectionAlignment.RIGHT
                with dsl.section(name=f"measure_{label}", alignment=SectionAlignment.LEFT):
                    sec = qop.measure(
                        qubit, dsl.handles.result_handle(qubit.uid, suffix=label)
                    )
                    sec.length = max_measure_section_length
                    qop.passive_reset(qubit)

    with dsl.acquire_loop_rt(
        count=opts.count,
        averaging_mode=opts.averaging_mode,
        acquisition_type=opts.acquisition_type,
        repetition_mode=opts.repetition_mode,
        repetition_time=opts.repetition_time,
        reset_oscillator_phase=opts.reset_oscillator_phase,
    ):
        if prepulse_amplitudes is None:
            _sequences()
        else:
            with dsl.sweep(
                name=f"prepulse_amplitude_sweep_{qubit.uid}",
                parameter=SweepParameter(
                    f"prepulse_amplitude_{qubit.uid}", prepulse_amplitudes
                ),
            ) as prepulse_amplitude:
                _sequences(prepulse_amplitude)


@workflow.workflow(name="population")
def population_experiment_workflow(
    session: Session,
    qpu: QPU,
    qubit: QuantumElements,
    prepulse_amplitudes: np.ndarray | None = None,
    temporary_parameters: dict[str, QuantumParameters] | None = None,
    options: PopulationWorkflowOptions | None = None,
) -> None:
    """The three-level population measurement workflow.

    Replaces the old
    `create_exp_population_full(x180, x180_ef, readout_opt, n_average)` +
    `my_session.compile()` + `my_session.run()` and, with
    `prepulse_amplitudes`, `make_exp_population_prepulse(pulse_sweep, ...)`.

    Arguments:
        session: The connected session to use for running the experiment.
        qpu: The QPU consisting of the qubits and quantum operations.
        qubit: The qubit to run the experiment on, passed by UID.
        prepulse_amplitudes: See `create_population_experiment`.
        temporary_parameters: The temporary parameters with which to update
            the quantum elements before running the experiment.
        options: `PopulationWorkflowOptions`.
    """
    temp_qpu = temporary_qpu(qpu, temporary_parameters)
    qubit = temporary_quantum_elements_from_qpu(temp_qpu, qubit)
    exp = create_population_experiment(
        temp_qpu,
        qubit,
        prepulse_amplitudes=prepulse_amplitudes,
    )
    compiled_exp = compile_experiment(session, exp)
    result = run_experiment(session, compiled_exp)
    workflow.return_(result)
