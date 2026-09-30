"""Three-level population experiment with a continuous flux drive.

The six-sequence three-level protocol (see
`POPULATION_SEQUENCES` below) with a flux pulse played continuously
around/between every sequence (old `make_exp_population_flux`,
`## Population with Flux Drive` and `## T1 and Population vs. Flux
Simultaneously` of the original notebook).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from laboneq import workflow
from laboneq.simple import Experiment, Oscillator, SectionAlignment, dsl
from laboneq.workflow.tasks import compile_experiment, run_experiment
from laboneq_applications.core import validation
from laboneq_applications.experiments.options import BaseExperimentOptions
from laboneq_applications.tasks.parameter_updating import (
    temporary_qpu,
    temporary_quantum_elements_from_qpu,
)

from qubit_thermometry.workflow.experiments.flux_amplitude_calibration import (
    FastFluxWorkflowOptions,
)

if TYPE_CHECKING:
    from laboneq.dsl.experiment.pulse import Pulse
    from laboneq.dsl.quantum import QuantumParameters
    from laboneq.dsl.quantum.qpu import QPU
    from laboneq.dsl.quantum.quantum_element import QuantumElement
    from laboneq.dsl.session import Session

# The six sequences of the three-level protocol, as lists of pi-pulse
# transitions played before the readout:
#   x0: -                 (thermal state)
#   x1: X_ge
#   x2: X_ge, X_ef
#   y0: X_ef
#   y1: X_ef, X_ge
#   y2: X_ef, X_ge, X_ef
#
# This is a local copy of `workflow.experiments.population.POPULATION_SEQUENCES`
# (owned by a different, parallel agent) -- duplicated here on purpose so this
# module has no cross-dependency on that in-progress file.
POPULATION_SEQUENCES = {
    "x0": (),
    "x1": ("ge",),
    "x2": ("ge", "ef"),
    "y0": ("ef",),
    "y1": ("ef", "ge"),
    "y2": ("ef", "ge", "ef"),
}


@workflow.task
@dsl.qubit_experiment
def create_population_flux_experiment(
    qpu: QPU,
    qubit: QuantumElement,
    flux_pulse: Pulse,
    flux_amplitude: float = 1.0,
    flux_oscillator_frequency: float = 0.0,
    options: BaseExperimentOptions | None = None,
) -> Experiment:
    """Create the three-level population experiment with a continuous flux drive.

    Arguments:
        qpu: The QPU consisting of the qubits and quantum operations.
        qubit: The qubit to run the experiment on.
        flux_pulse: The flux pulse played between/around every sequence
            (old `flux_pulse`, length ~ `reset_delay_length`).
        flux_amplitude: Amplitude of the flux pulse.
        flux_oscillator_frequency: Baseline oscillator frequency of the flux
            line (old `qubit_parameters["th_res_freq"]`).
        options: `BaseExperimentOptions`.

    Returns:
        experiment:
            The generated LabOne Q experiment instance to be compiled and executed.
    """
    opts = BaseExperimentOptions() if options is None else options
    qubit = validation.validate_and_convert_single_qubit_sweeps(qubit)

    qop = qpu.quantum_operations
    max_measure_section_length = qpu.measure_section_length([qubit])

    calibration = dsl.experiment_calibration()
    calibration[qubit.signals["flux"]].oscillator = Oscillator(
        frequency=flux_oscillator_frequency
    )

    def _flux_idle(name):
        with dsl.section(name=name):
            dsl.play(qubit.signals["flux"], pulse=flux_pulse, amplitude=flux_amplitude)

    with dsl.acquire_loop_rt(
        count=opts.count,
        averaging_mode=opts.averaging_mode,
        acquisition_type=opts.acquisition_type,
        repetition_mode=opts.repetition_mode,
        repetition_time=opts.repetition_time,
        reset_oscillator_phase=opts.reset_oscillator_phase,
    ):
        _flux_idle("flux_idle_start")
        for label, transitions in POPULATION_SEQUENCES.items():
            with dsl.section(name=f"main_{label}", alignment=SectionAlignment.RIGHT):
                if transitions:
                    with dsl.section(name=f"drive_{label}",
                                     alignment=SectionAlignment.RIGHT):
                        for transition in transitions:
                            sec = qop.x180(qubit, transition=transition)
                            sec.alignment = SectionAlignment.RIGHT
                with dsl.section(name=f"measure_{label}",
                                 alignment=SectionAlignment.LEFT):
                    sec = qop.measure(
                        qubit,
                        dsl.handles.result_handle(qubit.uid, suffix=label),
                    )
                    sec.length = max_measure_section_length
            _flux_idle(f"flux_idle_{label}")


@workflow.workflow(name="population_flux")
def population_flux_experiment_workflow(
    session: Session,
    qpu: QPU,
    qubit: str,
    flux_pulse: Pulse,
    flux_amplitude: float = 1.0,
    flux_oscillator_frequency: float = 0.0,
    temporary_parameters: dict[str, dict | QuantumParameters] | None = None,
    options: FastFluxWorkflowOptions | None = None,
) -> None:
    """The population-with-flux-drive workflow (old `make_exp_population_flux`).

    Arguments:
        session: The connected session to use for running the experiment.
        qpu: The QPU consisting of the original qubits and quantum operations.
        qubit: The qubit to run the experiment on, passed by UID.
        flux_pulse: The flux pulse played between/around every sequence.
        flux_amplitude: Amplitude of the flux pulse.
        flux_oscillator_frequency: Baseline oscillator frequency of the flux line.
        temporary_parameters: Temporary parameter overrides applied via
            `temporary_qpu`.
        options: `FastFluxWorkflowOptions`.
    """
    temp_qpu = temporary_qpu(qpu, temporary_parameters)
    qubit = temporary_quantum_elements_from_qpu(temp_qpu, qubit)
    exp = create_population_flux_experiment(
        temp_qpu,
        qubit,
        flux_pulse=flux_pulse,
        flux_amplitude=flux_amplitude,
        flux_oscillator_frequency=flux_oscillator_frequency,
    )
    compiled_exp = compile_experiment(session, exp)
    result = run_experiment(session, compiled_exp)
    workflow.return_(result)
