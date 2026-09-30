"""Flux/th_res amplitude-calibration experiment and workflow.

Sweeps the flux-pulse amplitude; an x180 pulse is played right-aligned
together with the flux pulse, followed by a delay before readout. The qubit
drive can be detuned from `resonance_frequency_ge` so that repeating the
sweep over a range of detunings builds a 2D detuning-vs-flux-amplitude map
(old `make_th_res_amp`, `## Flux Amplitude Calibration` and
`## Flux Pulse Check` of the original notebook).

`FastFluxWorkflowOptions` is shared by every Fast Flux Drive experiment
workflow in this package (`fast_flux_decay`, `population_flux`): there is no
`analysis_workflow` for these experiments, so only the options of the
`create_experiment` task (`count`, `averaging_mode`, ...) are relevant.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from laboneq import workflow
from laboneq.simple import (
    Experiment,
    Oscillator,
    SectionAlignment,
    SweepParameter,
    dsl,
)
from laboneq.workflow.tasks import compile_experiment, run_experiment
from laboneq_applications.core import validation
from laboneq_applications.experiments.options import BaseExperimentOptions
from laboneq_applications.tasks.parameter_updating import (
    temporary_qpu,
    temporary_quantum_elements_from_qpu,
)

if TYPE_CHECKING:
    from laboneq.dsl.experiment.pulse import Pulse
    from laboneq.dsl.quantum import QuantumParameters
    from laboneq.dsl.quantum.qpu import QPU
    from laboneq.dsl.quantum.quantum_element import QuantumElement
    from laboneq.dsl.session import Session

    from laboneq_applications.typing import QubitSweepPoints


@workflow.workflow_options
class FastFluxWorkflowOptions:
    """Options for the Fast Flux Drive experiment workflows.

    There is no analysis workflow for these experiments, so only the options
    of the `create_experiment` task (`count`, `averaging_mode`, ...) are
    relevant.
    """


@workflow.task
@dsl.qubit_experiment
def create_flux_amplitude_calibration_experiment(
    qpu: QPU,
    qubit: QuantumElement,
    flux_amplitudes: QubitSweepPoints,
    flux_pulse: Pulse,
    flux_detuning: float = 0.0,
    flux_oscillator_frequency: float = 0.0,
    delay_time: float = 1e-7,
    options: BaseExperimentOptions | None = None,
) -> Experiment:
    """Create the flux/th_res amplitude-calibration experiment.

    Sweeps the flux-pulse amplitude; an x180 pulse is played right-aligned
    together with the flux pulse, followed by `delay_time` before readout
    (old `exp_tr_amp.delay(signal="drive", time=delay_time)`).

    Arguments:
        qpu: The QPU consisting of the qubits and quantum operations.
        qubit: The qubit to run the experiment on.
        flux_amplitudes: The flux-pulse amplitudes to sweep over
            (old `res_amp_sweep`).
        flux_pulse: The flux pulse to play (old `gaussian_pulse` /
            `flux_pulse`, a `pulse_library.gaussian_square(...)` object).
        flux_detuning: Detuning of the qubit drive relative to
            `resonance_frequency_ge`, applied with `qop.set_frequency`
            (old `detune_ss` / the `"drive"` entry of `make_th_res_calib`).
        flux_oscillator_frequency: Baseline oscillator frequency of the flux
            line (old `qubit_parameters["th_res_freq"]`).
        delay_time: Delay between the x180 pulse and readout.
        options: `BaseExperimentOptions`.

    Returns:
        experiment:
            The generated LabOne Q experiment instance to be compiled and executed.
    """
    opts = BaseExperimentOptions() if options is None else options
    qubit, flux_amplitudes = validation.validate_and_convert_single_qubit_sweeps(
        qubit, flux_amplitudes
    )

    qop = qpu.quantum_operations
    max_measure_section_length = qpu.measure_section_length([qubit])

    calibration = dsl.experiment_calibration()
    calibration[qubit.signals["flux"]].oscillator = Oscillator(
        frequency=flux_oscillator_frequency
    )
    if flux_detuning:
        qop.set_frequency(
            qubit, qubit.parameters.resonance_frequency_ge + flux_detuning,
            transition="ge",
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
            name=f"flux_amplitude_sweep_{qubit.uid}",
            parameter=SweepParameter(f"flux_amplitude_{qubit.uid}", flux_amplitudes),
        ) as flux_amplitude:
            with dsl.section(name="main", alignment=SectionAlignment.RIGHT):
                with dsl.section(name="flux_and_drive", alignment=SectionAlignment.RIGHT):
                    dsl.play(qubit.signals["flux"], pulse=flux_pulse, amplitude=flux_amplitude)
                    sec = qop.x180(qubit)
                    sec.alignment = SectionAlignment.RIGHT
                    qop.delay(qubit, delay_time)
                with dsl.section(name="measure", alignment=SectionAlignment.LEFT):
                    sec = qop.measure(
                        qubit, dsl.handles.result_handle(qubit.uid, suffix="flux_amp")
                    )
                    sec.length = max_measure_section_length
                    qop.passive_reset(qubit)


@workflow.workflow(name="flux_amplitude_calibration")
def flux_amplitude_calibration_experiment_workflow(
    session: Session,
    qpu: QPU,
    qubit: str,
    flux_amplitudes: QubitSweepPoints,
    flux_pulse: Pulse,
    flux_detuning: float = 0.0,
    flux_oscillator_frequency: float = 0.0,
    delay_time: float = 1e-7,
    temporary_parameters: dict[str, dict | QuantumParameters] | None = None,
    options: FastFluxWorkflowOptions | None = None,
) -> None:
    """The flux/th_res amplitude-calibration workflow (old `make_th_res_amp`).

    Arguments:
        session: The connected session to use for running the experiment.
        qpu: The QPU consisting of the original qubits and quantum operations.
        qubit: The qubit to run the experiment on, passed by UID.
        flux_amplitudes: The flux-pulse amplitudes to sweep over.
        flux_pulse: The flux pulse to play.
        flux_detuning: Detuning of the qubit drive relative to
            `resonance_frequency_ge`.
        flux_oscillator_frequency: Baseline oscillator frequency of the flux line.
        delay_time: Delay between the x180 pulse and readout.
        temporary_parameters: Temporary parameter overrides applied via
            `temporary_qpu`.
        options: `FastFluxWorkflowOptions`.
    """
    temp_qpu = temporary_qpu(qpu, temporary_parameters)
    qubit = temporary_quantum_elements_from_qpu(temp_qpu, qubit)
    exp = create_flux_amplitude_calibration_experiment(
        temp_qpu,
        qubit,
        flux_amplitudes=flux_amplitudes,
        flux_pulse=flux_pulse,
        flux_detuning=flux_detuning,
        flux_oscillator_frequency=flux_oscillator_frequency,
        delay_time=delay_time,
    )
    compiled_exp = compile_experiment(session, exp)
    result = run_experiment(session, compiled_exp)
    workflow.return_(result)
