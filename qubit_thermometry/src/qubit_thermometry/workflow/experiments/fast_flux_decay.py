"""T1-decay-under-flux-detuning experiment and workflow.

Plays an x180 pulse, then a flux pulse whose *length* is the swept T1 delay,
then reads out -- i.e. T1 is measured while the qubit sits detuned by the
flux/th_res drive (old `make_fast_flux_decay`, `## Decay with Different Flux
Detuning` and `## T1 and Population vs. Flux Simultaneously` of the original
notebook).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from laboneq import workflow
from laboneq.simple import Experiment, Oscillator, SectionAlignment, SweepParameter, dsl
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

    from laboneq_applications.typing import QubitSweepPoints


@workflow.task
@dsl.qubit_experiment
def create_fast_flux_decay_experiment(
    qpu: QPU,
    qubit: QuantumElement,
    delays: QubitSweepPoints,
    flux_pulse: Pulse,
    flux_amplitude: float = 1.0,
    flux_oscillator_frequency: float = 0.0,
    options: BaseExperimentOptions | None = None,
) -> Experiment:
    """Create the T1-decay-under-flux-detuning experiment.

    Plays an x180 pulse, then a flux pulse whose *length* is the swept T1
    delay, then reads out -- i.e. T1 is measured while the qubit sits
    detuned by the flux/th_res drive (old `make_fast_flux_decay`).

    Arguments:
        qpu: The QPU consisting of the qubits and quantum operations.
        qubit: The qubit to run the experiment on.
        delays: The flux-pulse (T1 delay) lengths to sweep over
            (old `t1_sweep` / `t1_ff_sweep`).
        flux_pulse: The flux pulse to play, whose length is overridden by
            `delays` (old `flux_pulse`, a `pulse_library.const(...)` or
            `pulse_library.gaussian_square(..., can_compress=True)` object).
        flux_amplitude: Amplitude of the flux pulse.
        flux_oscillator_frequency: Baseline oscillator frequency of the flux
            line (old `qubit_parameters["th_res_freq"]`).
        options: `BaseExperimentOptions`.

    Returns:
        experiment:
            The generated LabOne Q experiment instance to be compiled and executed.
    """
    opts = BaseExperimentOptions() if options is None else options
    qubit, delays = validation.validate_and_convert_single_qubit_sweeps(qubit, delays)

    qop = qpu.quantum_operations
    max_measure_section_length = qpu.measure_section_length([qubit])

    calibration = dsl.experiment_calibration()
    calibration[qubit.signals["flux"]].oscillator = Oscillator(
        frequency=flux_oscillator_frequency
    )

    with dsl.acquire_loop_rt(
        count=opts.count,
        averaging_mode=opts.averaging_mode,
        acquisition_type=opts.acquisition_type,
        repetition_mode=opts.repetition_mode,
        repetition_time=opts.repetition_time,
        reset_oscillator_phase=opts.reset_oscillator_phase,
    ):
        with dsl.sweep(
            name=f"flux_decay_sweep_{qubit.uid}",
            parameter=SweepParameter(f"flux_decay_delay_{qubit.uid}", delays),
        ) as delay:
            with dsl.section(name="main", alignment=SectionAlignment.RIGHT):
                with dsl.section(name="drive", alignment=SectionAlignment.RIGHT):
                    sec = qop.x180(qubit)
                    sec.alignment = SectionAlignment.RIGHT
                with dsl.section(name="flux", alignment=SectionAlignment.RIGHT):
                    dsl.play(qubit.signals["flux"], pulse=flux_pulse,
                            amplitude=flux_amplitude, length=delay)
                with dsl.section(name="measure", alignment=SectionAlignment.LEFT):
                    sec = qop.measure(
                        qubit, dsl.handles.result_handle(qubit.uid, suffix="ff_decay")
                    )
                    sec.length = max_measure_section_length
                    qop.passive_reset(qubit)


@workflow.workflow(name="fast_flux_decay")
def fast_flux_decay_experiment_workflow(
    session: Session,
    qpu: QPU,
    qubit: str,
    delays: QubitSweepPoints,
    flux_pulse: Pulse,
    flux_amplitude: float = 1.0,
    flux_oscillator_frequency: float = 0.0,
    temporary_parameters: dict[str, dict | QuantumParameters] | None = None,
    options: FastFluxWorkflowOptions | None = None,
) -> None:
    """The T1-decay-under-flux-detuning workflow (old `make_fast_flux_decay`).

    Arguments:
        session: The connected session to use for running the experiment.
        qpu: The QPU consisting of the original qubits and quantum operations.
        qubit: The qubit to run the experiment on, passed by UID.
        delays: The flux-pulse (T1 delay) lengths to sweep over.
        flux_pulse: The flux pulse to play, whose length is overridden by `delays`.
        flux_amplitude: Amplitude of the flux pulse.
        flux_oscillator_frequency: Baseline oscillator frequency of the flux line.
        temporary_parameters: Temporary parameter overrides applied via
            `temporary_qpu`.
        options: `FastFluxWorkflowOptions`.
    """
    temp_qpu = temporary_qpu(qpu, temporary_parameters)
    qubit = temporary_quantum_elements_from_qpu(temp_qpu, qubit)
    exp = create_fast_flux_decay_experiment(
        temp_qpu,
        qubit,
        delays=delays,
        flux_pulse=flux_pulse,
        flux_amplitude=flux_amplitude,
        flux_oscillator_frequency=flux_oscillator_frequency,
    )
    compiled_exp = compile_experiment(session, exp)
    result = run_experiment(session, compiled_exp)
    workflow.return_(result)
