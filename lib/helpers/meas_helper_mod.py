# 
# This file is a wrapper for qubit measurements
# Here are make_ functions for the main experiments
#
#%config IPCompleter.greedy=True

# convenience import for all QCCS software functionality
from laboneq.simple import *

# helper import - needed to extract qubit and readout parameters from measurement data
#from tuneup_helper import *

#really needed imports
import numpy as np

#imports which can be needed
#from scipy.io import savemat, loadmat
#from YokoGS200_wrapper import YokoGS200
import matplotlib.pyplot as plt

#######################################################################################################
#calibration functions for frequency sweep experiments
def readout_calib(readout):
    exp_calibration = Calibration()
    exp_calibration["measure"] = SignalCalibration(
        # for spectroscopy, use the hardware oscillator of the QA, and set the sweep parameter as frequency
        oscillator=Oscillator(
            "measure_osc", frequency=readout['measure_freq'], modulation_type=ModulationType.SOFTWARE
        ),
        range = readout['readout_range']
    )
    exp_calibration["acquire"] = SignalCalibration(
        # for spectroscopy, use the hardware oscillator of the QA, and set the sweep parameter as frequency
        oscillator=Oscillator(
            "acquire_osc", frequency=readout['acquire_freq'], modulation_type=ModulationType.SOFTWARE
        ),
        port_delay = readout['readout_delay']
    )
    return exp_calibration

def long_readout_calib(readout):
    exp_calibration = Calibration()
    exp_calibration['measure'] = SignalCalibration(
        oscillator=Oscillator('long_measure_osc', frequency=readout['measure_freq'], modulation_type=ModulationType.HARDWARE)
    )

    exp_calibration['acquire'] = SignalCalibration(
        oscillator=Oscillator('long_acquire_osc', frequency=readout['acquire_freq'], modulation_type=ModulationType.HARDWARE)
    )

    return exp_calibration


def res_spec_calib(freq_sweep):
    exp_calibration = Calibration()
    # sets the oscillator of the experimental measure signal
    exp_calibration["measure"] = SignalCalibration(
        # for spectroscopy, use the hardware oscillator of the QA, and set the sweep parameter as frequency
        oscillator=Oscillator(
            "readout_osc", frequency=freq_sweep, modulation_type=ModulationType.HARDWARE
        )
    )
    return exp_calibration

def qubit_spec_calib(freq_sweep):
    exp_calibration = Calibration()
    # sets the oscillator of the experimental measure signal
    exp_calibration["drive"] = SignalCalibration(
        # for spectroscopy, use the hardware oscillator of the QA, and set the sweep parameter as frequency
        oscillator=Oscillator(
            "drive_osc", frequency=freq_sweep, modulation_type=ModulationType.HARDWARE
        )
    )
    return exp_calibration

def qubit_ef_spec_calib(freq_sweep):
    exp_calibration = Calibration()
    # sets the oscillator of the experimental measure signal
    exp_calibration["drive_ef"] = SignalCalibration(
        # for spectroscopy, use the hardware oscillator of the QA, and set the sweep parameter as frequency
        oscillator=Oscillator(
            "drive_ef_osc", frequency=freq_sweep, modulation_type=ModulationType.HARDWARE
        )
    )
    return exp_calibration

def make_ramsey_calib(freq, detuning):
    exp_calibration = Calibration()
    # sets the oscillator of the experimental measure signal
    exp_calibration["drive"] = SignalCalibration(
        # for spectroscopy, use the hardware oscillator of the QA, and set the sweep parameter as frequency
        oscillator=Oscillator(
            "drive_osc", frequency=freq+detuning, modulation_type=ModulationType.HARDWARE
        )
    )
    return exp_calibration

def make_ramsey_ef_calib(freq, detuning):
    exp_calibration = Calibration()
    # sets the oscillator of the experimental measure signal
    exp_calibration["drive_ef"] = SignalCalibration(
        # for spectroscopy, use the hardware oscillator of the QA, and set the sweep parameter as frequency
        oscillator=Oscillator(
            "drive_ef_osc", frequency=freq+detuning, modulation_type=ModulationType.HARDWARE
        )
    )
    return exp_calibration

def make_th_res_calib(th_res_freq, qb_freq, detuning):
    exp_calibration = Calibration()
    exp_calibration["th_res"] = SignalCalibration(
        oscillator=Oscillator(
            frequency=th_res_freq,
            modulation_type=ModulationType.HARDWARE,
        )
    )
    exp_calibration["drive"] = SignalCalibration(
        oscillator=Oscillator(
            frequency=qb_freq+detuning,
            modulation_type=ModulationType.HARDWARE,
        )
    )
    return exp_calibration

def make_fast_flux_calib(th_res_freq, qb_freq, detuning, lo_freq):
    exp_calibration = Calibration()
    exp_calibration["th_res"] = SignalCalibration(
        oscillator=Oscillator(
            frequency=th_res_freq,
            modulation_type=ModulationType.HARDWARE,
        ),
        # local_oscillator=Oscillator(
        #     frequency=lo_freq,        # LO signal, 4-8 GHz range
        # )
    )
    exp_calibration["drive"] = SignalCalibration(
        oscillator=Oscillator(
            frequency=qb_freq+detuning,
            modulation_type=ModulationType.HARDWARE,
        ),
        local_oscillator=Oscillator(
            frequency=lo_freq,        # LO signal, 4-8 GHz range
        )
    )
    return exp_calibration


#######################################################################################################
# signal maps

#Measure-Aquuire signal map (for simple one-tone spectroscopy)
MA_map = {
    "measure": "/logical_signal_groups/q0/measure",
    "acquire": "/logical_signal_groups/q0/acquire",
}

# signal map for qubit exitation and measurement (spectroscopy)
qubit_meas_map = {
    "drive": "/logical_signal_groups/q0/drive",
    "measure": "/logical_signal_groups/q0/measure",
    "acquire": "/logical_signal_groups/q0/acquire",
}

# signal map for ef-measurements only (spectroscopy)
qubit_ef_only_map = {
    "drive_ef": "/logical_signal_groups/q0/drive_ef_line",
    "measure": "/logical_signal_groups/q0/measure",
    "acquire": "/logical_signal_groups/q0/acquire",
}

qubit_ef_map = {
    "drive": "/logical_signal_groups/q0/drive",
    "drive_ef": "/logical_signal_groups/q0/drive_ef_line",
    "measure": "/logical_signal_groups/q0/measure",
    "acquire": "/logical_signal_groups/q0/acquire",
}

qubit_resonator_map = {
    "drive": "/logical_signal_groups/q0/drive",
    "th_res": "/logical_signal_groups/q0/th_res",
    "measure": "/logical_signal_groups/q0/measure",
    "acquire": "/logical_signal_groups/q0/acquire",
}

qubit_all_map = {
    "drive": "/logical_signal_groups/q0/drive",
    "drive_ef": "/logical_signal_groups/q0/drive_ef_line",
    "th_res": "/logical_signal_groups/q0/th_res",
    "measure": "/logical_signal_groups/q0/measure",
    "acquire": "/logical_signal_groups/q0/acquire",
}
#######################################################################################################
#default qubit readout pulse - here simple constant pulse
readout_pulse_def = pulse_library.const(
    uid="readout_pulse",
    length=2e-6,
    amplitude=0.6,
)
# defaultintegration weights for qubit measurement - here simple constant weights, i.e. all parts of the return signal are weighted equally
readout_weighting_function_def = pulse_library.const(
    uid="readout_weighting_function", length=2e-6, amplitude=1.0
)

#######################################################################################################
#function that return two points helper sweep
def make_two_point_sweep(start = 0.0, stop = 1.0):
    sweep_2 = LinearSweepParameter(
        uid="rabi_amp", start=start, stop=stop, count=2
    )
    return sweep_2

#######################################################################################################
# function that modifies an experiment by adding the qubit readout and signal acquisition sections
def readoutQubit(
    exp,
    section_id="qubit_readout",
    readout_id="q0_measure",
    acquire_id="q0_acquire",
    acquire_handle="q0_acquire",
    play_after_section=None,
    reserve_id=None,
    readout_pulse=readout_pulse_def,
    readout_weights=readout_weighting_function_def,
    relax_time=20e-6,
    delay_uid='delay',
    acquire_length=None
):
    # section for readout pulse and data acquisition
    with exp.section(uid=section_id, play_after = play_after_section):
        # reserve drive line for duration of readout and data acquisition - if selected
        if reserve_id is not None:
            exp.reserve(signal=reserve_id)
        # play readout pulse on measure line
        exp.play(signal=readout_id, pulse=readout_pulse)
        # trigger signal data acquisition
        exp.acquire(
            signal=acquire_id,
            handle=acquire_handle,
            kernel=readout_weights,
            length=acquire_length
        )
    with exp.section(uid=delay_uid, play_after=section_id):
        # relax time after readout - for qubit relaxation to groundstate and signal processing
        exp.delay(signal=readout_id, time=relax_time)
        # make sure that the drive line is reserved also for the relax time, if selected
        if reserve_id is not None:
            exp.reserve(signal=reserve_id)


def long_readout_qubit(
    exp,
    section_id="qubit_readout",
    readout_id="q0_measure",
    acquire_id="q0_acquire",
    acquire_handle="q0_acquire",
    play_after_section=None,
    reserve_id=None,
    readout_pulse=readout_pulse_def,
    readout_weights=readout_weighting_function_def,
    relax_time=20e-6,
    delay_uid='delay'
):

    assert readout_pulse.can_compress, "The readout pulse has to be compressible to use the long readout function!"




#######################################################################################################
# function that returns an amplitude Rabi experiment
def make_rabi(rabi_sweep, gaussian_pulse, readout_pulse, readout_weighting_function, relax_time, n_average):
    exp_rabi = Experiment(
        uid="Amplitude Rabi",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define Rabi experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_rabi.acquire_loop_rt(
        uid="rabi_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        # inner loop - real time sweep of Rabi ampitudes
        with exp_rabi.sweep(uid="rabi_sweep", parameter=rabi_sweep):
            # play qubit excitation pulse - pulse amplitude is swept
            with exp_rabi.section(uid="qubit_excitation"):
                exp_rabi.play(signal="drive", pulse=gaussian_pulse, amplitude=rabi_sweep)
            # readout pulse and data acquisition
            readoutQubit(
                exp_rabi,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_rabi",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )
    return exp_rabi

# function that returns ge pulse repetition experiment
def make_pulse_repetition(pulse, N_sweep, readout_pulse, readout_weighting_function, relax_time, n_average):
    exp_pulse_rep = Experiment(
        uid="Pulse Repetition",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_pulse_rep.acquire_loop_rt(
        uid="pulse_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        with exp_pulse_rep.sweep(uid="N_sweep", parameter=N_sweep):
            # inner loop - real time sweep of N
            with exp_pulse_rep.section(uid="qubit_excitation"):
                for i in range(N_sweep.values):
                    exp_pulse_rep.play(signal="drive", pulse=pulse)
            # readout pulse and data acquisition
            readoutQubit(
                exp_pulse_rep,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_rep",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )
    return exp_pulse_rep

# function that returns single shot Rabi experiment
def make_rabi_SS(rabi_sweep, gaussian_pulse, readout_pulse, readout_weighting_function, relax_time, n_average):
    exp_rabi_SS = Experiment(
        uid="Single Shots",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define Rabi experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_rabi_SS.acquire_loop_rt(
        uid="rabi_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.SINGLE_SHOT,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        # inner loop - real time sweep of Rabi ampitudes
        with exp_rabi_SS.sweep(uid="rabi_sweep", parameter=rabi_sweep):
            # play qubit excitation pulse - pulse amplitude is swept
            with exp_rabi_SS.section(uid="qubit_excitation"):
                exp_rabi_SS.play(signal="drive", pulse=gaussian_pulse, amplitude=rabi_sweep)
            # readout pulse and data acquisition
            readoutQubit(
                exp_rabi_SS,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="SS_rabi",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )
    return exp_rabi_SS

# function that returns single shot experiments
def make_shots(state, x_180, x_180_ef, readout_pulse, readout_weighting_function, relax_time, n_average):
    exp_SS = Experiment(
        uid="Single Shots",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("drive_ef"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define Rabi experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_SS.acquire_loop_rt(
        uid="S_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.SINGLE_SHOT,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        # inner loop
        if state == 'e':
            with exp_SS.section(uid="qubit_excitation"):
                exp_SS.play(signal="drive", pulse=x_180)
        elif state == 'f':
            with exp_SS.section(uid="ge_excitation"):
                exp_SS.play(signal="drive", pulse=x_180)
                exp_SS.delay(signal = 'drive', time = 10e-9)
            with exp_SS.section(uid="ef_excitation", play_after = "ge_excitation"):
                exp_SS.play(signal="drive_ef", pulse=x_180_ef)
        elif state == 'g':
            with exp_SS.section(uid="qubit_excitation"):
                exp_SS.play(signal="drive", pulse=x_180, amplitude = 0.0)
        else:
            print('Wrong state for single shots!')
        # readout pulse and data acquisition
        readoutQubit(
            exp_SS,
            section_id="qubit_readout",
            readout_id="measure",
            acquire_id="acquire",
            reserve_id="drive",
            acquire_handle="shots",
            readout_pulse=readout_pulse,
            readout_weights=readout_weighting_function,
            relax_time=relax_time,
        )
    return exp_SS

# function that returns an amplitude Rabi experiment for ef-levels with ONE ge pulse (prepulse)
def make_rabi_ef_1(rabi_ef_sweep, gaussian_pulse, readout_pulse, readout_weighting_function, relax_time, n_average, x180, ge_amp = 0.0):
    exp_rabi_ef_1 = Experiment(
        uid="Amplitude ef-Rabi (one)",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("drive_ef"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define Rabi experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_rabi_ef_1.acquire_loop_rt(
        uid="rabi_ef_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION
    ):
        # inner loop - real time sweep of Rabi ampitudes
        with exp_rabi_ef_1.sweep(uid="rabi_ef_sweep", parameter=rabi_ef_sweep):
            # inner loop - real time sweep of Rabi ampitudes
            with exp_rabi_ef_1.section(uid = 'excitation_ge'):
                exp_rabi_ef_1.play(signal = 'drive', pulse = x180, amplitude=ge_amp)
                exp_rabi_ef_1.delay(signal = 'drive', time = 10e-9)
            with exp_rabi_ef_1.section(uid = 'excitation_ef', play_after = 'excitation_ge'):
                exp_rabi_ef_1.play(signal = 'drive_ef', pulse = gaussian_pulse, amplitude=rabi_ef_sweep)
            # readout pulse and data acquisition
            readoutQubit(
                exp_rabi_ef_1,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_rabi_ef",
                play_after_section = 'excitation_ef',
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )
    return exp_rabi_ef_1

# function that returns an amplitude Rabi experiment for ef-levels with TWO ge pulses
def make_rabi_ef_2(rabi_ef_sweep, gaussian_pulse, readout_pulse, readout_weighting_function, relax_time, n_average, x180, ge_amp = 0.0):
    exp_rabi_ef_2 = Experiment(
        uid="Amplitude ef-Rabi (two)",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("drive_ef"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define Rabi experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_rabi_ef_2.acquire_loop_rt(
        uid="rabi_ef_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION
    ):
        # inner loop - real time sweep of Rabi ampitudes
        with exp_rabi_ef_2.sweep(uid="rabi_ef_sweep", parameter=rabi_ef_sweep):
            # inner loop - real time sweep of Rabi ampitudes
            with exp_rabi_ef_2.section(uid = 'excitation_ge'):
                exp_rabi_ef_2.play(signal = 'drive', pulse = x180, amplitude=ge_amp)
                exp_rabi_ef_2.delay(signal = 'drive', time = 10e-9)
            with exp_rabi_ef_2.section(uid = 'excitation_ef', play_after = 'excitation_ge'):
                exp_rabi_ef_2.play(signal = 'drive_ef', pulse = gaussian_pulse, amplitude=rabi_ef_sweep)
                exp_rabi_ef_2.delay(signal = 'drive_ef', time = 10e-9)
            with exp_rabi_ef_2.section(uid = 'excitation_ge_2', play_after = 'excitation_ef'):
                exp_rabi_ef_2.play(signal = 'drive', pulse = x180, amplitude=ge_amp)
            # readout pulse and data acquisition
            readoutQubit(
                exp_rabi_ef_2,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_rabi_ef",
                play_after_section = 'excitation_ef',
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )
    return exp_rabi_ef_2

# function that returns a T1-measurement experiment
def make_t1(t1_sweep, x180, readout_pulse, readout_weighting_function, relax_time, n_average):
    exp_t1 = Experiment(
        uid="Qubit T1",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define experiment sequence
    # outer loop - real-time, cyclic averaging
    with exp_t1.acquire_loop_rt(
        uid="t1_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        # inner loop - real-time sweep of delay between pi-pulse and readout
        with exp_t1.sweep(uid="t1_sweep", parameter=t1_sweep):
            # qubit pi pulse and following delay - use right aligned section of constant length for optimised timing behavior
            with exp_t1.section(
                uid="qubit_excitation",
                #length=t1_sweep.stop + 2 * x180.length,
                alignment=SectionAlignment.RIGHT,
            ):
                exp_t1.play(signal="drive", pulse=x180)
                exp_t1.delay(signal="drive", time=t1_sweep)
            # readout pulse and data acquisition
            readoutQubit(
                exp_t1,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_t1",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )
            
    return exp_t1

# function that returns a T1-measurement experiment for ef-level with ONE ge-prepulse
def make_T1_ef_1(t1_ef_sweep, x180_ef, readout_pulse, readout_weighting_function, relax_time, n_average, x180, ge_amp = 0.0):
    exp_T1_ef_1 = Experiment(
        uid="Decay on ef",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("drive_ef"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define Rabi experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_T1_ef_1.acquire_loop_rt(
        uid="decay_ef_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION
    ):
        # inner loop - real time sweep of Rabi ampitudes
        with exp_T1_ef_1.sweep(uid="rabi_ef_sweep", parameter=t1_ef_sweep):
            # inner loop - real time sweep of Rabi ampitudes
            with exp_T1_ef_1.section(uid = 'excitation_ge'):
                exp_T1_ef_1.play(signal = 'drive', pulse = x180, amplitude=ge_amp)
                exp_T1_ef_1.delay(signal = 'drive', time = 10e-9)
            with exp_T1_ef_1.section(uid = 'excitation_ef', play_after = 'excitation_ge'):
                exp_T1_ef_1.play(signal = 'drive_ef', pulse = x180_ef)
                exp_T1_ef_1.delay(signal = 'drive_ef', time = t1_ef_sweep)
            # readout pulse and data acquisition
            readoutQubit(
                exp_T1_ef_1,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_t1_ef",
                play_after_section = 'excitation_ef',
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )
    return exp_T1_ef_1

# function that returns a Ramsey experiment
def make_ramsey(ramsey_sweep, x90, readout_pulse, readout_weighting_function, relax_time, n_average):
    exp_ramsey = Experiment(
        uid="Ramsey",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define Experiment sequence
    # outer loop - real-time, cyclic averaging
    with exp_ramsey.acquire_loop_rt(
        uid="ramsey_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        # inner loop - sweep Ramsey delay in real time
        with exp_ramsey.sweep(uid="ramsey_sweep", parameter=ramsey_sweep):
            # Ramsey pulse sequence on qubit - use right-aligned, constant length section for optimised timing behavior
            with exp_ramsey.section(
                uid="qubit_excitation",
                length=ramsey_sweep.stop + 2 * x90.length,
                alignment=SectionAlignment.RIGHT,
            ):
                exp_ramsey.play(signal="drive", pulse=x90)
                exp_ramsey.delay(signal="drive", time=ramsey_sweep)
                exp_ramsey.play(signal="drive", pulse=x90)
            # readout pulse and data acquisition
            readoutQubit(
                exp_ramsey,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                acquire_handle="q0_ramsey",
                play_after_section = "qubit_excitation",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )
            
    return exp_ramsey

# function that returns a Ramsey experiment on ef-transition with TWO ge pulses
def make_ramsey_ef_2(ramsey_ef_sweep, x90_ef, readout_pulse, readout_weighting_function, relax_time, n_average, x180, ge_amp = 0.0):
    exp_ramsey_ef_2 = Experiment(
        uid="Ramsey on ef",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("drive_ef"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define Rabi experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_ramsey_ef_2.acquire_loop_rt(
        uid="ramsey_ef_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION
    ):
        # inner loop - real time sweep of Rabi ampitudes
        with exp_ramsey_ef_2.sweep(uid="ramsey_ef_sweep", parameter=ramsey_ef_sweep):
            # inner loop - real time sweep of Rabi ampitudes
            with exp_ramsey_ef_2.section(uid = 'excitation_ge'):
                exp_ramsey_ef_2.play(signal = 'drive', pulse = x180, amplitude=ge_amp)
                exp_ramsey_ef_2.delay(signal = 'drive', time = 10e-9)
            with exp_ramsey_ef_2.section(uid = 'ef_ramsey', play_after = 'excitation_ge'):
                exp_ramsey_ef_2.play(signal = 'drive_ef', pulse = x90_ef)
                exp_ramsey_ef_2.delay(signal='drive_ef', time=ramsey_ef_sweep)
                exp_ramsey_ef_2.play(signal = 'drive_ef', pulse = x90_ef)
                exp_ramsey_ef_2.delay(signal = 'drive_ef', time = 10e-9)
            with exp_ramsey_ef_2.section(uid = 'excitation_ge_2', play_after = 'ef_ramsey'):
                exp_ramsey_ef_2.play(signal = 'drive', pulse = x180, amplitude=ge_amp)
            # readout pulse and data acquisition
            readoutQubit(
                exp_ramsey_ef_2,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_ramsey_ef",
                play_after_section = 'excitation_ge_2',
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )
    return exp_ramsey_ef_2

# function that returns a Hahn-echo experiment
def make_echo(echo_sweep, x90, x180, readout_pulse, readout_weighting_function, relax_time, n_average):
    exp_echo = Experiment(
        uid="Echo",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define Experiment sequence
    # outer loop - real-time, cyclic averaging
    with exp_echo.acquire_loop_rt(
        uid="echo_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        # inner loop - sweep Ramsey delay in real time
        with exp_echo.sweep(uid="echo_sweep", parameter=echo_sweep):
            # Ramsey pulse sequence on qubit - use right-aligned, constant length section for optimised timing behavior
            with exp_echo.section(
                uid="qubit_excitation",
                length=2*echo_sweep.stop + 2 * x90.length + x180.length,
                alignment=SectionAlignment.RIGHT,
            ):
                exp_echo.play(signal="drive", pulse=x90)
                exp_echo.delay(signal="drive", time=echo_sweep)
                exp_echo.play(signal="drive", pulse=x180)
                exp_echo.delay(signal="drive", time=echo_sweep)
                exp_echo.play(signal="drive", pulse=x90)
            # readout pulse and data acquisition
            readoutQubit(
                exp_echo,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_echo",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )
            
    return exp_echo
########################################################################################################
#Population measurements experiments

# function that returns a population measurement experiment
def make_exp_population(x180, x180_ef, readout_pulse, readout_weighting_function, relax_time, n_average):
    # sweep between two points - 0.0 and 1.0
    count = 2
    start = 0.0
    stop = 1.0

    two_points_sweep_1 = LinearSweepParameter(
        uid="two_points_sweep_1", start=start, stop=stop, count=count
    )

    two_points_sweep_2 = LinearSweepParameter(
        uid="two_points_sweep_2", start=start, stop=stop, count=count
    )

    two_points_sweep_3 = LinearSweepParameter(
        uid="two_points_sweep_3", start=start, stop=stop, count=count
    )

    two_points_sweep_4 = LinearSweepParameter(
        uid="two_points_sweep_4", start=start, stop=stop, count=count
    )
    
    # experiment with two-dimentional sweep
    #for measurement x0, x1, x2, y0, y1
    
    exp_population = Experiment(
        uid="Population meas",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("drive_ef"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    # outer loop - real-time, cyclic averaging
    with exp_population.acquire_loop_rt(
        uid="population_meas",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION
    ):
        # inner loop - real time sweep of Rabi ampitudes
        with exp_population.sweep(uid="sweep1", parameter=[two_points_sweep_1, two_points_sweep_3]):
            with exp_population.sweep(uid="sweep2", parameter=[two_points_sweep_2, two_points_sweep_4]):
                # inner loop
                # first sequence and readout
                with exp_population.section(uid = 'first_pulse'):
                    exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=two_points_sweep_1)
                    exp_population.delay(signal = 'drive_ef', time = 10e-9)
                with exp_population.section(uid = 'second_pulse', play_after = 'first_pulse'):
                    exp_population.play(signal = 'drive', pulse = x180, amplitude=two_points_sweep_2)
                # first readout pulse and data acquisition
                with exp_population.section(uid='readout1', play_after = 'second_pulse'):
                    # play readout pulse on measure line
                    exp_population.play(signal='measure', pulse=readout_pulse)
                    # trigger signal data acquisition
                    exp_population.acquire(
                        signal='acquire',
                        handle='first_readout',
                        kernel=readout_weighting_function,
                    )
                with exp_population.section(uid="relax_delay1", play_after='readout1'):
                    # relax time after readout - for qubit relaxation to groundstate and signal processing
                    exp_population.delay(signal='measure', time=relax_time)
                #
                # second sequence and readout
                with exp_population.section(uid = 'third_pulse', play_after = "relax_delay1"):
                    exp_population.play(signal = 'drive', pulse = x180, amplitude=two_points_sweep_3)
                    exp_population.delay(signal = 'drive', time = 10e-9)
                with exp_population.section(uid = 'fourth_pulse', play_after = 'third_pulse'):
                    exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=two_points_sweep_4)
                # second readout pulse and data acquisition
                with exp_population.section(uid='readout2', play_after = 'fourth_pulse'):
                    # play readout pulse on measure line
                    exp_population.play(signal='measure', pulse=readout_pulse)
                    # trigger signal data acquisition
                    exp_population.acquire(
                        signal='acquire',
                        handle='second_readout',
                        kernel=readout_weighting_function,
                    )
                with exp_population.section(uid="relax_delay2", play_after='readout2'):
                    # relax time after readout - for qubit relaxation to groundstate and signal processing
                    exp_population.delay(signal='measure', time=relax_time)
                    
    return exp_population

#function that return full population experiment
def make_exp_population_full(x180, x180_ef, readout_pulse, readout_weighting_function, relax_time, n_average):
       
    # experiment with two-dimentional sweep
    #for measurement x0, x1, x2, y0, y1, y2
    
    exp_population = Experiment(
        uid="Population meas",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("drive_ef"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    # outer loop - real-time, cyclic averaging
    with exp_population.acquire_loop_rt(
        uid="population_meas",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION
    ):
        # inner loop
        # x0 sequence and readout
        with exp_population.section(uid='readout_x0'):
            # play readout pulse on measure line
            exp_population.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_population.acquire(
                signal='acquire',
                handle='x0_readout',
                kernel=readout_weighting_function,
                )
        with exp_population.section(uid="relax_x0", play_after='readout_x0'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_population.delay(signal='measure', time=relax_time)
        
        # x1 sequence and readout
        with exp_population.section(uid = 'x1_pulse', play_after = 'relax_x0'):
            exp_population.play(signal = 'drive', pulse = x180, amplitude=1)
            # first readout pulse and data acquisition
        with exp_population.section(uid='readout_x1', play_after = 'x1_pulse'):
            # play readout pulse on measure line
            exp_population.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_population.acquire(
                signal='acquire',
                handle='x1_readout',
                kernel=readout_weighting_function,
                )
        with exp_population.section(uid="relax_x1", play_after='readout_x1'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_population.delay(signal='measure', time=relax_time)
            
        # x2 sequence and readout
        with exp_population.section(uid = 'x2_pulse_ge', play_after = 'relax_x1'):
            exp_population.play(signal = 'drive', pulse = x180, amplitude=1)
            exp_population.delay(signal = 'drive', time = 10e-9)
        with exp_population.section(uid = 'x2_pulse_ef', play_after = 'x2_pulse_ge'):
            exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
            # first readout pulse and data acquisition
        with exp_population.section(uid='readout_x2', play_after = 'x2_pulse_ef'):
            # play readout pulse on measure line
            exp_population.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_population.acquire(
                signal='acquire',
                handle='x2_readout',
                kernel=readout_weighting_function,
                )
        with exp_population.section(uid="relax_x2", play_after='readout_x2'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_population.delay(signal='measure', time=relax_time)  
            
        # y0 sequence and readout
        with exp_population.section(uid = 'y0_pulse', play_after = 'relax_x2'):
            exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
        with exp_population.section(uid='readout_y0', play_after = 'y0_pulse'):
            # play readout pulse on measure line
            exp_population.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_population.acquire(
                signal='acquire',
                handle='y0_readout',
                kernel=readout_weighting_function,
                )
        with exp_population.section(uid="relax_y0", play_after='readout_y0'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_population.delay(signal='measure', time=relax_time)
        
        # y1 sequence and readout
        with exp_population.section(uid = 'y1_pulse_ef', play_after = 'relax_y0'):
            exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
            exp_population.delay(signal = 'drive_ef', time = 10e-9)
        with exp_population.section(uid = 'y1_pulse_ge', play_after = 'y1_pulse_ef'):
            exp_population.play(signal = 'drive', pulse = x180, amplitude=1)
            # first readout pulse and data acquisition
        with exp_population.section(uid='readout_y1', play_after = 'y1_pulse_ge'):
            # play readout pulse on measure line
            exp_population.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_population.acquire(
                signal='acquire',
                handle='y1_readout',
                kernel=readout_weighting_function,
                )
        with exp_population.section(uid="relax_y1", play_after='readout_y1'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_population.delay(signal='measure', time=relax_time)
            
        # y2 sequence and readout
        with exp_population.section(uid = 'y2_pulse_ef1', play_after = 'relax_y1'):
            exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
            exp_population.delay(signal = 'drive_ef', time = 10e-9)
        with exp_population.section(uid = 'y2_pulse_ge', play_after = 'y2_pulse_ef1'):
            exp_population.play(signal = 'drive', pulse = x180, amplitude=1)
            exp_population.delay(signal = 'drive', time = 10e-9)
        with exp_population.section(uid = 'y2_pulse_ef2', play_after = 'y2_pulse_ge'):
            exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
            # first readout pulse and data acquisition
        with exp_population.section(uid='readout_y2', play_after = 'y2_pulse_ef2'):
            # play readout pulse on measure line
            exp_population.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_population.acquire(
                signal='acquire',
                handle='y2_readout',
                kernel=readout_weighting_function,
                )
        with exp_population.section(uid="relax_y2", play_after='readout_y2'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_population.delay(signal='measure', time=relax_time)
                    
    return exp_population

#function that return full population experiment
def make_exp_population_flux(x180, x180_ef, flux_pulse, readout_pulse, readout_weighting_function, relax_time, n_average):
       
    # experiment with two-dimentional sweep
    #for measurement x0, x1, x2, y0, y1, y2
    
    exp_population = Experiment(
        uid="Population FF meas",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("drive_ef"),
            ExperimentSignal("th_res"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    # outer loop - real-time, cyclic averaging
    with exp_population.acquire_loop_rt(
        uid="population_ff_meas",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION
    ):
        # inner loop
        # x0 sequence and readout
        with exp_population.section(uid="relax_before"):
            exp_population.play(signal='th_res', pulse=flux_pulse)
        with exp_population.section(uid='readout_x0', play_after="relax_before"):
            # play readout pulse on measure line
            exp_population.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_population.acquire(
                signal='acquire',
                handle='x0_readout',
                kernel=readout_weighting_function,
                )
        with exp_population.section(uid="relax_x0", play_after='readout_x0'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_population.play(signal='th_res', pulse=flux_pulse)
        
        # x1 sequence and readout
        with exp_population.section(uid = 'x1_pulse', play_after = 'relax_x0'):
            exp_population.play(signal = 'drive', pulse = x180, amplitude=1)
            # first readout pulse and data acquisition
        with exp_population.section(uid='readout_x1', play_after = 'x1_pulse'):
            # play readout pulse on measure line
            exp_population.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_population.acquire(
                signal='acquire',
                handle='x1_readout',
                kernel=readout_weighting_function,
                )
        with exp_population.section(uid="relax_x1", play_after='readout_x1'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_population.play(signal='th_res', pulse=flux_pulse)
            
        # x2 sequence and readout
        with exp_population.section(uid = 'x2_pulse_ge', play_after = 'relax_x1'):
            exp_population.play(signal = 'drive', pulse = x180, amplitude=1)
            exp_population.delay(signal = 'drive', time = 10e-9)
        with exp_population.section(uid = 'x2_pulse_ef', play_after = 'x2_pulse_ge'):
            exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
            # first readout pulse and data acquisition
        with exp_population.section(uid='readout_x2', play_after = 'x2_pulse_ef'):
            # play readout pulse on measure line
            exp_population.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_population.acquire(
                signal='acquire',
                handle='x2_readout',
                kernel=readout_weighting_function,
                )
        with exp_population.section(uid="relax_x2", play_after='readout_x2'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_population.play(signal='th_res', pulse=flux_pulse)  
            
        # y0 sequence and readout
        with exp_population.section(uid = 'y0_pulse', play_after = 'relax_x2'):
            exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
        with exp_population.section(uid='readout_y0', play_after = 'y0_pulse'):
            # play readout pulse on measure line
            exp_population.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_population.acquire(
                signal='acquire',
                handle='y0_readout',
                kernel=readout_weighting_function,
                )
        with exp_population.section(uid="relax_y0", play_after='readout_y0'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_population.play(signal='th_res', pulse=flux_pulse)
        
        # y1 sequence and readout
        with exp_population.section(uid = 'y1_pulse_ef', play_after = 'relax_y0'):
            exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
            exp_population.delay(signal = 'drive_ef', time = 10e-9)
        with exp_population.section(uid = 'y1_pulse_ge', play_after = 'y1_pulse_ef'):
            exp_population.play(signal = 'drive', pulse = x180, amplitude=1)
            # first readout pulse and data acquisition
        with exp_population.section(uid='readout_y1', play_after = 'y1_pulse_ge'):
            # play readout pulse on measure line
            exp_population.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_population.acquire(
                signal='acquire',
                handle='y1_readout',
                kernel=readout_weighting_function,
                )
        with exp_population.section(uid="relax_y1", play_after='readout_y1'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_population.play(signal='th_res', pulse=flux_pulse)
            
        # y2 sequence and readout
        with exp_population.section(uid = 'y2_pulse_ef1', play_after = 'relax_y1'):
            exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
            exp_population.delay(signal = 'drive_ef', time = 10e-9)
        with exp_population.section(uid = 'y2_pulse_ge', play_after = 'y2_pulse_ef1'):
            exp_population.play(signal = 'drive', pulse = x180, amplitude=1)
            exp_population.delay(signal = 'drive', time = 10e-9)
        with exp_population.section(uid = 'y2_pulse_ef2', play_after = 'y2_pulse_ge'):
            exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
            # first readout pulse and data acquisition
        with exp_population.section(uid='readout_y2', play_after = 'y2_pulse_ef2'):
            # play readout pulse on measure line
            exp_population.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_population.acquire(
                signal='acquire',
                handle='y2_readout',
                kernel=readout_weighting_function,
                )
        with exp_population.section(uid="relax_y2", play_after='readout_y2'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_population.play(signal='th_res', pulse=flux_pulse)
                    
    return exp_population

#function that return full population experiment
def make_exp_pop_correlations(x180, r_delay, readout_pulse, readout_weighting_function, relax_time, n_average):
    
    exp_pop_corr = Experiment(
        uid="Population correlations meas",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    # outer loop - real-time, cyclic averaging
    with exp_pop_corr.acquire_loop_rt(
        uid="pop_corr_meas",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.SINGLE_SHOT,
        acquisition_type=AcquisitionType.INTEGRATION
    ):
        # inner loop
        # x0 sequence and readout
        with exp_pop_corr.section(uid='readout_1'):
            # play readout pulse on measure line
            exp_pop_corr.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_pop_corr.acquire(
                signal='acquire',
                handle='readout_1',
                kernel=readout_weighting_function,
                )
        with exp_pop_corr.section(uid="delay1", play_after='readout_1'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_pop_corr.delay(signal='measure', time=r_delay)
        with exp_pop_corr.section(uid='readout_2', play_after='delay1'):
            # play readout pulse on measure line
            exp_pop_corr.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_pop_corr.acquire(
                signal='acquire',
                handle='readout_2',
                kernel=readout_weighting_function,
                )
        with exp_pop_corr.section(uid="relax_1", play_after='readout_2'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_pop_corr.delay(signal='measure', time=relax_time)

        #round 2 - with pi pulse
        with exp_pop_corr.section(uid = 'pi_pulse', play_after = 'relax_1'):
            exp_pop_corr.play(signal = 'drive', pulse = x180, amplitude=1)
            # first readout pulse and data acquisition
        with exp_pop_corr.section(uid='readout_pi1', play_after = 'pi_pulse'):
            # play readout pulse on measure line
            exp_pop_corr.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_pop_corr.acquire(
                signal='acquire',
                handle='readout_pi1',
                kernel=readout_weighting_function,
                )
        with exp_pop_corr.section(uid="delay2", play_after='readout_pi1'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_pop_corr.delay(signal='measure', time=r_delay)
        with exp_pop_corr.section(uid='readout_pi2', play_after='delay2'):
            # play readout pulse on measure line
            exp_pop_corr.play(signal='measure', pulse=readout_pulse)
            # trigger signal data acquisition
            exp_pop_corr.acquire(
                signal='acquire',
                handle='readout_pi2',
                kernel=readout_weighting_function,
                )
        with exp_pop_corr.section(uid="relax_2", play_after='readout_pi2'):
            # relax time after readout - for qubit relaxation to groundstate and signal processing
            exp_pop_corr.delay(signal='measure', time=relax_time)
                    
    return exp_pop_corr

def make_exp_pop_correlation_continuous_ro(x180, r_delay, readout_pulse, readout_weighting_function, relax_time, n_average):
    raise NotImplementedError
    pass

#function that return the population experiment with prepulse
def make_exp_population_prepulse(pulse_sweep, x180, x180_ef, gaussian_pulse, readout_pulse, readout_weighting_function, relax_time, n_average):
       
    # experiment with two-dimentional sweep
    #for measurement x0, x1, x2, y0, y1, y2
    
    exp_population = Experiment(
        uid="Population meas",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("drive_ef"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    # outer loop - real-time, cyclic averaging
    with exp_population.acquire_loop_rt(
        uid="population_meas",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION
    ):
        with exp_population.sweep(uid="pulse_sweep", parameter=pulse_sweep):
        # inner loop
            # x0 sequence and readout
            with exp_population.section(uid="qubit_excitation1"):
                exp_population.play(signal="drive", pulse=gaussian_pulse, amplitude=pulse_sweep)
                exp_population.delay(signal = 'drive', time = 10e-9)
            with exp_population.section(uid='readout_x0', play_after='qubit_excitation1'):
                # play readout pulse on measure line
                exp_population.play(signal='measure', pulse=readout_pulse)
                # trigger signal data acquisition
                exp_population.acquire(
                    signal='acquire',
                    handle='x0_readout',
                    kernel=readout_weighting_function,
                    )
            with exp_population.section(uid="relax_x0", play_after='readout_x0'):
                # relax time after readout - for qubit relaxation to groundstate and signal processing
                exp_population.delay(signal='measure', time=relax_time)
        
            # x1 sequence and readout
            with exp_population.section(uid="qubit_excitation2", play_after = 'relax_x0'):
                exp_population.play(signal="drive", pulse=gaussian_pulse, amplitude=pulse_sweep)
                exp_population.delay(signal = 'drive', time = 10e-9)
            with exp_population.section(uid = 'x1_pulse', play_after = 'qubit_excitation2'):
                exp_population.play(signal = 'drive', pulse = x180, amplitude=1)
                # first readout pulse and data acquisition
            with exp_population.section(uid='readout_x1', play_after = 'x1_pulse'):
                # play readout pulse on measure line
                exp_population.play(signal='measure', pulse=readout_pulse)
                # trigger signal data acquisition
                exp_population.acquire(
                    signal='acquire',
                    handle='x1_readout',
                    kernel=readout_weighting_function,
                    )
            with exp_population.section(uid="relax_x1", play_after='readout_x1'):
                # relax time after readout - for qubit relaxation to groundstate and signal processing
                exp_population.delay(signal='measure', time=relax_time)
            
            # x2 sequence and readout
            with exp_population.section(uid="qubit_excitation3", play_after = 'relax_x1'):
                exp_population.play(signal="drive", pulse=gaussian_pulse, amplitude=pulse_sweep)
                exp_population.delay(signal = 'drive', time = 10e-9)
            with exp_population.section(uid = 'x2_pulse_ge', play_after = 'qubit_excitation3'):
                exp_population.play(signal = 'drive', pulse = x180, amplitude=1)
                exp_population.delay(signal = 'drive', time = 10e-9)
            with exp_population.section(uid = 'x2_pulse_ef', play_after = 'x2_pulse_ge'):
                exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
                # first readout pulse and data acquisition
            with exp_population.section(uid='readout_x2', play_after = 'x2_pulse_ef'):
                # play readout pulse on measure line
                exp_population.play(signal='measure', pulse=readout_pulse)
                # trigger signal data acquisition
                exp_population.acquire(
                    signal='acquire',
                    handle='x2_readout',
                    kernel=readout_weighting_function,
                    )
            with exp_population.section(uid="relax_x2", play_after='readout_x2'):
                # relax time after readout - for qubit relaxation to groundstate and signal processing
                exp_population.delay(signal='measure', time=relax_time)  
            
            # y0 sequence and readout
            with exp_population.section(uid="qubit_excitation4", play_after = 'relax_x2'):
                exp_population.play(signal="drive", pulse=gaussian_pulse, amplitude=pulse_sweep)
                exp_population.delay(signal = 'drive', time = 10e-9)
            with exp_population.section(uid = 'y0_pulse', play_after = 'qubit_excitation4'):
                exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
            with exp_population.section(uid='readout_y0', play_after = 'y0_pulse'):
                # play readout pulse on measure line
                exp_population.play(signal='measure', pulse=readout_pulse)
                # trigger signal data acquisition
                exp_population.acquire(
                    signal='acquire',
                    handle='y0_readout',
                    kernel=readout_weighting_function,
                    )
            with exp_population.section(uid="relax_y0", play_after='readout_y0'):
                # relax time after readout - for qubit relaxation to groundstate and signal processing
                exp_population.delay(signal='measure', time=relax_time)
        
            # y1 sequence and readout
            with exp_population.section(uid="qubit_excitation5", play_after = 'relax_y0'):
                exp_population.play(signal="drive", pulse=gaussian_pulse, amplitude=pulse_sweep)
                exp_population.delay(signal = 'drive', time = 10e-9)
            with exp_population.section(uid = 'y1_pulse_ef', play_after = 'qubit_excitation5'):
                exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
                exp_population.delay(signal = 'drive_ef', time = 10e-9)
            with exp_population.section(uid = 'y1_pulse_ge', play_after = 'y1_pulse_ef'):
                exp_population.play(signal = 'drive', pulse = x180, amplitude=1)
                # first readout pulse and data acquisition
            with exp_population.section(uid='readout_y1', play_after = 'y1_pulse_ge'):
                # play readout pulse on measure line
                exp_population.play(signal='measure', pulse=readout_pulse)
                # trigger signal data acquisition
                exp_population.acquire(
                    signal='acquire',
                    handle='y1_readout',
                    kernel=readout_weighting_function,
                    )
            with exp_population.section(uid="relax_y1", play_after='readout_y1'):
                # relax time after readout - for qubit relaxation to groundstate and signal processing
                exp_population.delay(signal='measure', time=relax_time)
            
            # y2 sequence and readout
            with exp_population.section(uid="qubit_excitation6", play_after = 'relax_y1'):
                exp_population.play(signal="drive", pulse=gaussian_pulse, amplitude=pulse_sweep)
                exp_population.delay(signal = 'drive', time = 10e-9)
            with exp_population.section(uid = 'y2_pulse_ef1', play_after = 'qubit_excitation6'):
                exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
                exp_population.delay(signal = 'drive_ef', time = 10e-9)
            with exp_population.section(uid = 'y2_pulse_ge', play_after = 'y2_pulse_ef1'):
                exp_population.play(signal = 'drive', pulse = x180, amplitude=1)
                exp_population.delay(signal = 'drive', time = 10e-9)
            with exp_population.section(uid = 'y2_pulse_ef2', play_after = 'y2_pulse_ge'):
                exp_population.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
                # first readout pulse and data acquisition
            with exp_population.section(uid='readout_y2', play_after = 'y2_pulse_ef2'):
                # play readout pulse on measure line
                exp_population.play(signal='measure', pulse=readout_pulse)
                # trigger signal data acquisition
                exp_population.acquire(
                    signal='acquire',
                    handle='y2_readout',
                    kernel=readout_weighting_function,
                    )
            with exp_population.section(uid="relax_y2", play_after='readout_y2'):
                # relax time after readout - for qubit relaxation to groundstate and signal processing
                exp_population.delay(signal='measure', time=relax_time)
                    
    return exp_population

#Rabi population measurements
def get_rabi_population_calibration_measurement(theta_ef_sweep, gaussian_pulse, readout_pulse, readout_weighting_function, relax_time, n_average, x180):
    exp_rpm = Experiment(
        uid="Rabi Population Measurement no pre pulse",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("drive_ef"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ]
    )

    ## define RPM experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_rpm.acquire_loop_rt(
        uid="rpm_averaging_wo",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION
    ):
        # inner loop - real time sweep of ef amplitudes
        # without ge pre-pulse 
        with exp_rpm.sweep(uid="theta_ef_sweep_wo", parameter=theta_ef_sweep):
            with exp_rpm.section(uid='theta_ef_wo'):
                exp_rpm.play(signal='drive_ef', pulse=gaussian_pulse, amplitude=theta_ef_sweep)
                exp_rpm.delay(signal = 'drive_ef', time = 10e-9)
            with exp_rpm.section(uid = 'excitation_ge_wo', play_after='theta_ef_wo'):
                exp_rpm.play(signal = 'drive', pulse = x180, amplitude=1.0)

            # readout pulse and data acquisition
            readoutQubit(
                exp_rpm,
                section_id="qubit_readout_wo",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="rpm_wo",
                play_after_section = 'excitation_ge_wo',
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
                delay_uid='delay_wo'
            )

            # with ge pre-pulse

            with exp_rpm.section(uid = 'excitation_ge_one_with', play_after='delay_wo'):
                exp_rpm.play(signal = 'drive', pulse = x180, amplitude=1.0)
                exp_rpm.delay(signal = 'drive', time = 10e-9)
            with exp_rpm.section(uid='theta_ef_with', play_after='excitation_ge_one_with'):
                exp_rpm.play(signal='drive_ef', pulse=gaussian_pulse, amplitude=theta_ef_sweep)
                exp_rpm.delay(signal = 'drive_ef', time = 10e-9)
            with exp_rpm.section(uid = 'excitation_ge_two_with', play_after='theta_ef_with'):
                exp_rpm.play(signal = 'drive', pulse = x180, amplitude=1.0)

            # readout pulse and data acquisition
            readoutQubit(
                exp_rpm,
                section_id="qubit_readout_with",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="rpm_with",
                play_after_section = 'excitation_ge_two_with',
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
                delay_uid='delay_with'
            )
            
    return exp_rpm

def get_quick_rabi_population_measurement(rpm_x180_ef_pulse, rep_count, gaussian_pulse, readout_pulse, readout_weighting_function, relax_time, n_average, x180):
    exp_rpm = Experiment(
        uid="Rabi Population Measurement no pre pulse",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("drive_ef"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ]
    )
    
    mock_sweep = LinearSweepParameter(uid="mock_sweep", start=0, stop=1, count=rep_count)

    ## define RPM experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_rpm.acquire_loop_rt(
        uid="rpm_averaging",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION
    ):
        
        with exp_rpm.sweep(uid="mock_sweep_section", parameter=mock_sweep):
            # without ge pre-pulse 
            # measure minimum point
            with exp_rpm.section(uid='theta_ef_wo_min'):
                exp_rpm.play(signal='drive_ef', pulse=gaussian_pulse, amplitude=0)
                exp_rpm.delay(signal = 'drive_ef', time = 10e-9)
            with exp_rpm.section(uid = 'excitation_ge_wo_min', play_after='theta_ef_wo_min'):
                exp_rpm.play(signal = 'drive', pulse = x180, amplitude=1.0)

            # readout pulse and data acquisition
            readoutQubit(
                exp_rpm,
                section_id="qubit_readout_wo_min",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="rpm_wo_min",
                play_after_section = 'excitation_ge_wo_min',
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
                delay_uid='delay_wo_min'
            )

            # measure maximum point
            with exp_rpm.section(uid='theta_ef_wo_max', play_after='delay_wo_min'):
                exp_rpm.play(signal='drive_ef', pulse=rpm_x180_ef_pulse, amplitude=1)
                exp_rpm.delay(signal = 'drive_ef', time = 10e-9)
            with exp_rpm.section(uid = 'excitation_ge_wo_max', play_after='theta_ef_wo_max'):
                exp_rpm.play(signal = 'drive', pulse = x180, amplitude=1.0)

            # readout pulse and data acquisition
            readoutQubit(
                exp_rpm,
                section_id="qubit_readout_wo_max",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="rpm_wo_max",
                play_after_section = 'excitation_ge_wo_max',
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
                delay_uid='delay_wo_max'
            )

            # with ge pre-pulse
            # minimum point
            with exp_rpm.section(uid = 'excitation_ge_one_with_min', play_after='delay_wo_max'):
                exp_rpm.play(signal = 'drive', pulse = x180, amplitude=1.0)
                exp_rpm.delay(signal = 'drive', time = 10e-9)
            with exp_rpm.section(uid = 'excitation_ge_two_with_min', play_after='excitation_ge_one_with_min'):
                exp_rpm.play(signal = 'drive', pulse = x180, amplitude=1.0)

            # readout pulse and data acquisition
            readoutQubit(
                exp_rpm,
                section_id="qubit_readout_with_min",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="rpm_with_min",
                play_after_section = 'excitation_ge_two_with_min',
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
                delay_uid='delay_with_min'
            )

            # maximum point
            with exp_rpm.section(uid = 'excitation_ge_one_with_max', play_after='delay_with_min'):
                exp_rpm.play(signal = 'drive', pulse = x180, amplitude=1.0)
                exp_rpm.delay(signal = 'drive', time = 10e-9)
            with exp_rpm.section(uid='theta_ef_with_max', play_after='excitation_ge_one_with_max'):
                exp_rpm.play(signal='drive_ef', pulse=rpm_x180_ef_pulse, amplitude=1)
                exp_rpm.delay(signal = 'drive_ef', time = 10e-9)
            with exp_rpm.section(uid = 'excitation_ge_two_with_max', play_after='theta_ef_with_max'):
                exp_rpm.play(signal = 'drive', pulse = x180, amplitude=1.0)

            # readout pulse and data acquisition
            readoutQubit(
                exp_rpm,
                section_id="qubit_readout_with_max",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="rpm_with_max",
                play_after_section = 'excitation_ge_two_with_max',
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
                delay_uid='delay_with_max'
            )
            
    return exp_rpm

############################################################################################################

# function that defines a resonator spectroscopy experiment, and takes the frequency sweep as a parameter
def res_spectroscopy(freq_sweep, readout_pulse_spec, n_average):
    # Create resonator spectroscopy experiment - uses only readout drive and signal acquisition
    exp_spec = Experiment(
        uid="Resonator Spectroscopy",
        signals=[
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define experimental sequence
    # outer loop - vary drive frequency
    with exp_spec.sweep(uid="res_freq", parameter=freq_sweep):
        # inner loop - average multiple measurements for each frequency - measurement in spectroscopy mode
        with exp_spec.acquire_loop_rt(
            uid="shots",
            count=pow(2, n_average),
            acquisition_type=AcquisitionType.SPECTROSCOPY,
        ):
            # readout pulse and data acquisition
            with exp_spec.section(uid="spectroscopy"):
                # play resonator excitation pulse
                exp_spec.play(signal="measure", pulse=readout_pulse_spec)
                # resonator signal readout
                exp_spec.acquire(
                    signal="acquire",
                    handle="res_spec",
                    length=readout_pulse_spec.length, #qubit_parameters["ro_len_spec"],
                )
            with exp_spec.section(uid="delay", play_after="spectroscopy"):
                # holdoff time after signal acquisition - minimum 1us required for data processing on UHFQA
                exp_spec.delay(signal="measure", time=1e-6)

    return exp_spec

# function that defines a qubit spectroscopy experiment, and takes the frequency sweep as a parameter
def qubit_spectroscopy(freq_sweep, qubit_pulse, readout_pulse, readout_weighting_function, relax_time, n_average):
    # Create qubit spectroscopy Experiment - uses qubit drive, readout drive and data acquisition lines
    exp_qspec = Experiment(
        uid="Qubit Spectroscopy",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define experimental pulse sequence
    # outer loop - near time qubit drive frequency sweep
    with exp_qspec.sweep(
        uid="qfreq_sweep", parameter=freq_sweep, execution_type=ExecutionType.NEAR_TIME
    ):
        # inner loop - real-time averaging - QA in integration mode
        with exp_qspec.acquire_loop_rt(
            uid="qfreq_shots",
            count=pow(2, n_average),
            acquisition_type=AcquisitionType.INTEGRATION,
        ):
            # qubit drive
            with exp_qspec.section(uid="qubit_excitation"):
                exp_qspec.play(signal="drive", pulse=qubit_pulse)
            # readout pulse and data acquisition - use code section defined earlier
            readoutQubit(
                exp_qspec,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_spec",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )

    return exp_qspec


# function that returns a qubit spectroscopy experiment- accepts frequency sweep range as parameter
def qubit_ef_spectroscopy(freq_sweep, qubit_pulse, readout_pulse, readout_weighting_function, relax_time, n_average):
    # Create qubit spectroscopy Experiment - uses qubit drive, readout drive and data acquisition lines
    exp_ef_qspec = Experiment(
        uid="Qubit e-f Spectroscopy",
        signals=[
            ExperimentSignal("drive_ef"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define experimental pulse sequence
    # outer loop - near time qubit drive frequency sweep
    with exp_ef_qspec.sweep(
        uid="qfreq_ef_sweep", parameter=freq_sweep, execution_type=ExecutionType.NEAR_TIME
    ):
        # inner loop - real-time averaging - QA in integration mode
        with exp_ef_qspec.acquire_loop_rt(
            uid="qfreq_ef_shots",
            count=pow(2, n_average),
            acquisition_type=AcquisitionType.INTEGRATION,
        ):
            # qubit drive
            with exp_ef_qspec.section(uid="qubit_ef_excitation"):
                exp_ef_qspec.play(signal="drive_ef", pulse=qubit_pulse)
            # readout pulse and data acquisition - use code section defined earlier
            readoutQubit(
                exp_ef_qspec,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive_ef",
                acquire_handle="q0_ef_spec",
                play_after_section="qubit_ef_excitation",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )

    return exp_ef_qspec

# function that returns a qubit spectroscopy experiment- accepts frequency sweep range as parameter
def qubit_ef_spectroscopy_with_prepulse(freq_sweep, x180, qubit_pulse, readout_pulse, readout_weighting_function, relax_time, n_average):
    # Create qubit spectroscopy Experiment - uses qubit drive, readout drive and data acquisition lines
    exp_ef_qspec = Experiment(
        uid="Qubit e-f Spectroscopy_prep",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("drive_ef"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define experimental pulse sequence
    # outer loop - near time qubit drive frequency sweep
    with exp_ef_qspec.sweep(
        uid="qfreq_ef_sweep", parameter=freq_sweep, execution_type=ExecutionType.NEAR_TIME
    ):
        # inner loop - real-time averaging - QA in integration mode
        with exp_ef_qspec.acquire_loop_rt(
            uid="qfreq_ef_shots",
            count=pow(2, n_average),
            acquisition_type=AcquisitionType.INTEGRATION,
        ):
            # qubit drive
            with exp_ef_qspec.section(uid="qubit_ge_excitation"):
                exp_ef_qspec.play(signal="drive", pulse=x180)
                exp_ef_qspec.delay(signal="drive", time = 10e-9)
            with exp_ef_qspec.section(uid="qubit_ef_excitation", play_after ="qubit_ge_excitation"):
                exp_ef_qspec.play(signal="drive_ef", pulse=qubit_pulse)
            # readout pulse and data acquisition - use code section defined earlier
            readoutQubit(
                exp_ef_qspec,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive_ef",
                acquire_handle="q0_ef_spec",
                play_after_section="qubit_ef_excitation",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )

    return exp_ef_qspec
   
# function that defines a resonator spectroscopy experiment with/without pi_ge prepulse
def make_res_spec_e(freq_sweep, x180, readout_pulse, readout_weighting_function, relax_time, n_average, ge_amp):
    # Create resonator spectroscopy experiment - uses only readout drive and signal acquisition
    exp_spec_e = Experiment(
        uid="Resonator Spectroscopy for e-state",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define experimental sequence
    # outer loop - vary drive frequency
    with exp_spec_e.sweep(uid="res_freq", parameter=freq_sweep):
        # inner loop - average multiple measurements for each frequency - measurement in spectroscopy mode
        with exp_spec_e.acquire_loop_rt(
            uid="shots",
            count=pow(2, n_average),
            acquisition_type=AcquisitionType.SPECTROSCOPY,
        ):
            with exp_spec_e.section(uid="qubit_excitation"):
                exp_spec_e.play(signal="drive", pulse=x180, amplitude=ge_amp)
            readoutQubit(
                exp_spec_e,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_res_spec_e",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )

    return exp_spec_e

# function that defines a resonator spectroscopy experiment with pi_ge and pi_ef prepulses
def make_res_spec_f(freq_sweep, x180, x180_ef, readout_pulse, readout_weighting_function, relax_time, n_average):
    # Create resonator spectroscopy experiment - uses only readout drive and signal acquisition
    exp_spec_f = Experiment(
        uid="Resonator Spectroscopy for f-state",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("drive_ef"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define experimental sequence
    # outer loop - vary drive frequency
    with exp_spec_f.sweep(uid="res_freq", parameter=freq_sweep):
        # inner loop - average multiple measurements for each frequency - measurement in spectroscopy mode
        with exp_spec_f.acquire_loop_rt(
            uid="shots",
            count=pow(2, n_average),
            acquisition_type=AcquisitionType.SPECTROSCOPY,
        ):
            with exp_spec_f.section(uid="qubit_ge_excitation"):
                exp_spec_f.play(signal="drive", pulse=x180, amplitude=1)
                exp_spec_f.delay(signal = 'drive', time = 10e-9)
            with exp_spec_f.section(uid = 'qubit_ef_excitation', play_after = 'qubit_ge_excitation'):
                exp_spec_f.play(signal = 'drive_ef', pulse = x180_ef, amplitude=1)
            readoutQubit(
                exp_spec_f,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                acquire_handle="q0_res_spec_f",
                play_after_section = "qubit_ef_excitation",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )

    return exp_spec_f

# function that defines a resonator spectroscopy experiment with/without pi_ge prepulse
def make_res_spec_flux(freq_sweep, flux_pulse, x180, readout_pulse, readout_weighting_function, relax_time, n_average, ge_amp):
    # Create resonator spectroscopy experiment - uses only readout drive and signal acquisition
    exp_spec_flux = Experiment(
        uid="Resonator Spectroscopy with flux",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("th_res"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )
    ## define experimental sequence
    # outer loop - vary drive frequency
    with exp_spec_flux.sweep(uid="res_freq", parameter=freq_sweep):
        # inner loop - average multiple measurements for each frequency - measurement in spectroscopy mode
        with exp_spec_flux.acquire_loop_rt(
            uid="shots",
            count=pow(2, n_average),
            acquisition_type=AcquisitionType.SPECTROSCOPY,
        ):
            with exp_spec_flux.section(uid="flux_excitation", alignment=SectionAlignment.RIGHT):
                exp_spec_flux.play(signal="th_res", pulse=flux_pulse)
                exp_spec_flux.play(signal="drive", pulse=x180, amplitude=ge_amp)
                exp_spec_flux.delay(signal="drive", time=10e-9)
            readoutQubit(
                exp_spec_flux,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_res_spec_flux",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )

    return exp_spec_flux

#####################################################################################################
# experiments for resonator pumping
#####################################################################################################
# function that returns pi-pulse with delay measurement with thermal resonator frequency sweep
def make_th_res_amp(res_amp_sweep, gaussian_pulse, x180, readout_pulse, readout_weighting_function, relax_time, n_average, delay_time = 1e-6):
    exp_tr_amp = Experiment(
        uid="Th_res_amp",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("th_res"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define Rabi experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_tr_amp.acquire_loop_rt(
        uid="tr_amp_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        # inner loop - real time sweep of Rabi ampitudes
        with exp_tr_amp.sweep(uid="res_amp_sweep", parameter=res_amp_sweep, alignment=SectionAlignment.RIGHT):
            # play qubit excitation pulse - pulse amplitude is swept
            with exp_tr_amp.section(uid="th_res_pulse", alignment=SectionAlignment.RIGHT):
                exp_tr_amp.play(signal="th_res", pulse=gaussian_pulse, amplitude=res_amp_sweep)
            #with exp_tr_amp.section(uid="q_ex_pulse", alignment=SectionAlignment.RIGHT):
                exp_tr_amp.play(signal="drive", pulse=x180)
                exp_tr_amp.delay(signal="drive", time=delay_time)
            # readout pulse and data acquisition
            readoutQubit(
                exp_tr_amp,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_tr_amp",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )
    return exp_tr_amp

#####################################################################################################
###Functions for fast flux drive operations
#####################################################################################################
# function that measure qubit T1 while qubit is detuned
def make_fast_flux_decay(t1_sweep, flux_pulse, edge, x180, readout_pulse, readout_weighting_function, relax_time, n_average):
    exp_FF_decay = Experiment(
        uid="FFlux_full_decay",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("th_res"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define Rabi experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_FF_decay.acquire_loop_rt(
        uid="ff_decay_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        # inner loop - real time sweep of Rabi ampitudes
        with exp_FF_decay.sweep(uid="res_amp_sweep", parameter=t1_sweep):
            # play qubit excitation pulse
            with exp_FF_decay.section(uid="q_ex_pulse"):
                exp_FF_decay.play(signal="drive", pulse=x180)
            with exp_FF_decay.section(uid="flux_pulse", play_after="q_ex_pulse"):
                exp_FF_decay.play(signal="th_res", pulse=flux_pulse, length = t1_sweep)
            # readout pulse and data acquisition
            readoutQubit(
                exp_FF_decay,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_ff_decay",
                play_after_section = "flux_pulse",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )
    return exp_FF_decay

######################################################################################################

# function that measure qubit T1 during the thermal resonator pumping
def make_th_res_decay(t1_sweep, th_res_pulse, x180, readout_pulse, readout_weighting_function, relax_time, n_average):
    exp_tr_decay = Experiment(
        uid="Th_res_decay",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("th_res"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define Rabi experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_tr_decay.acquire_loop_rt(
        uid="tr_amp_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        # inner loop - real time sweep of Rabi ampitudes
        with exp_tr_decay.sweep(uid="res_amp_sweep", parameter=t1_sweep, alignment=SectionAlignment.RIGHT):
            # play qubit excitation pulse - pulse amplitude is swept
            with exp_tr_decay.section(uid="th_res_pulse", alignment=SectionAlignment.RIGHT):
                exp_tr_decay.play(signal="th_res", pulse=th_res_pulse)
            #with exp_tr_amp.section(uid="q_ex_pulse", alignment=SectionAlignment.RIGHT):
                exp_tr_decay.play(signal="drive", pulse=x180)
                exp_tr_decay.delay(signal="drive", time=t1_sweep)
            # readout pulse and data acquisition
            readoutQubit(
                exp_tr_decay,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_tr_decay",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )
    return exp_tr_decay

# function that measure Ramsey oscillations during the thermal resonator pumping
def make_th_res_ramsey(ramsey_sweep, th_res_pulse, x90, readout_pulse, readout_weighting_function, relax_time, n_average):
    exp_tr_ramsey = Experiment(
        uid="Th_res_ramsey",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("th_res"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define Rabi experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_tr_ramsey.acquire_loop_rt(
        uid="tr_ramsey_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        # inner loop - real time sweep of Rabi ampitudes
        with exp_tr_ramsey.sweep(uid="res_ramsey_sweep", parameter=ramsey_sweep, alignment=SectionAlignment.RIGHT):
            # play qubit excitation pulse - pulse amplitude is swept
            with exp_tr_ramsey.section(uid="th_res_pulse", alignment=SectionAlignment.RIGHT):
                exp_tr_ramsey.play(signal="th_res", pulse=th_res_pulse)
            #with exp_tr_amp.section(uid="q_ex_pulse", alignment=SectionAlignment.RIGHT):
                exp_tr_ramsey.play(signal="drive", pulse=x90)
                exp_tr_ramsey.delay(signal="drive", time=ramsey_sweep)
                exp_tr_ramsey.play(signal="drive", pulse=x90)
            # readout pulse and data acquisition
            readoutQubit(
                exp_tr_ramsey,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_tr_ramsey",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
            )
    return exp_tr_ramsey

def make_propagation_delay(delay_sweep, readout_pulse, acquire_length, relax_time, n_average):
    exp_prop_delay = Experiment(
        uid="Propagation Delay Measurement",
        signals=[
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    readout_weighting_function = pulse_library.const(
            uid="readout_weighting_function", length=acquire_length, amplitude=1.0
        )

    with exp_prop_delay.sweep(uid="del_sweep", parameter=delay_sweep):
        with exp_prop_delay.acquire_loop_rt(
            uid="shots",
            count=2**n_average,
            acquisition_type=AcquisitionType.INTEGRATION,
        ):
            # readout pulse and data acquisition
            readoutQubit(
                exp_prop_delay,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                acquire_handle="res_prop_delay",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time
            )

    cal = Calibration()
    cal["acquire"] = SignalCalibration(port_delay=delay_sweep)
    exp_prop_delay.set_calibration(cal)
    

    return exp_prop_delay

def repeat(count: int | SweepParameter | LinearSweepParameter, exp):
    def decorator(f):
        if isinstance(count, (LinearSweepParameter, SweepParameter)):
            with exp.match(sweep_parameter=count):
                for v in count.values:
                    with exp.case(v):
                        for _ in range(int(v)):
                            f()
        else:
            for _ in range(count):
                f()

    return decorator

def make_rabi_error_amplification(flips_sweep, x180, x90, readout_pulse, readout_weighting_function, relax_time, n_average, target_pulse):
    assert target_pulse in ['x90eg', 'x180eg'], f"Choose from {['x90eg', 'x180eg']}!"
    exp_rabi = Experiment(
        uid="Rabi Error Amplification",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    if target_pulse == 'x180eg':
        tpulse=x180
        preamp = 1

    elif target_pulse == 'x90eg':
        tpulse=x90
        preamp = 0
        print(f'Notice: For x90 calibration, use odd numbers of repetitions.')

    ## define Rabi experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_rabi.acquire_loop_rt(
        uid="rabi_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
             # readout pulse and data acquisition
        readoutQubit(
            exp_rabi,
            section_id="qubit_readout_calib_0",
            readout_id="measure",
            acquire_id="acquire",
            reserve_id="drive",
            acquire_handle="calib_0",
            readout_pulse=readout_pulse,
            readout_weights=readout_weighting_function,
            relax_time=relax_time,
            delay_uid='delay_0'
        )

        with exp_rabi.section(uid='calib_1_section', play_after='qubit_readout_calib_0'):
            exp_rabi.play(signal="drive", pulse=x180, amplitude=1)
             # readout pulse and data acquisition
        readoutQubit(
            exp_rabi,
            section_id="qubit_readout_calib_1",
            readout_id="measure",
            acquire_id="acquire",
            reserve_id="drive",
            acquire_handle="calib_1",
            readout_pulse=readout_pulse,
            readout_weights=readout_weighting_function,
            relax_time=relax_time,
            delay_uid='delay_1'
        )
        
        # apply a sequence of pi pulses
        with exp_rabi.sweep(uid="flip_sweeps", parameter=flips_sweep) as flips_count:
            with exp_rabi.section(uid='preparation'):
                exp_rabi.play(signal="drive", pulse=x90, amplitude=preamp)

            @repeat(flips_count, exp_rabi)
            def _pi_pulses():
                with exp_rabi.section():
                    exp_rabi.play(signal="drive", pulse=tpulse, amplitude=1)
            # readout pulse and data acquisition
            readoutQubit(
                exp_rabi,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_rabi",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                relax_time=relax_time,
                delay_uid='delay_2'
            )
    return exp_rabi

def make_rabi_error_amplification_ef(flips_sweep, x180, x90, x180ef, x90ef, readout_pulse, readout_weighting_function, relax_time, n_average, target_pulse):
    assert target_pulse in ['x90ef', 'x180ef'], f"Choose from {['x90ef', 'x180ef']}!"
    exp_rabi = Experiment(
        uid="Rabi Error Amplification",
        signals=[
            ExperimentSignal("drive"),
            ExperimentSignal("drive_ef"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    if target_pulse == 'x180ef':
        tpulse=x180ef
        preamp = 1

    elif target_pulse == 'x90ef':
        tpulse=x90ef
        preamp = 0
        print(f'Notice: For x90 calibration, use odd numbers of repetitions.')

    ## define Rabi experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_rabi.acquire_loop_rt(
        uid="rabi_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        with exp_rabi.section(uid='calib_0_section_a'):
            exp_rabi.play(signal="drive", pulse=x180, amplitude=1)
            exp_rabi.delay(signal='drive', time=10e-9)
        
        with exp_rabi.section(uid='calib_0_section_b', play_after='calib_0_section_a'):
            exp_rabi.play(signal="drive_ef", pulse=x180ef, amplitude=0)
            exp_rabi.delay(signal='drive_ef', time=10e-9)
            
        with exp_rabi.section(uid='calib_0_section_c', play_after='calib_0_section_b'):
            exp_rabi.play(signal="drive", pulse=x180, amplitude=1)
           
             # readout pulse and data acquisition
        readoutQubit(
            exp_rabi,
            section_id="qubit_readout_calib_0",
            readout_id="measure",
            acquire_id="acquire",
            reserve_id="drive",
            acquire_handle="calib_0",
            readout_pulse=readout_pulse,
            readout_weights=readout_weighting_function,
            relax_time=relax_time,
            delay_uid='delay_0'
        )

        with exp_rabi.section(uid='calib_1_section_a'):
            exp_rabi.play(signal="drive", pulse=x180, amplitude=1)
            exp_rabi.delay(signal='drive', time=10e-9)
        
        with exp_rabi.section(uid='calib_1_section_b', play_after='calib_1_section_a'):
            exp_rabi.play(signal="drive_ef", pulse=x180ef, amplitude=1)
            exp_rabi.delay(signal='drive_ef', time=10e-9)
            
        with exp_rabi.section(uid='calib_1_section_c', play_after='calib_1_section_b'):
            exp_rabi.play(signal="drive", pulse=x180, amplitude=1)
            
        # readout pulse and data acquisition
        readoutQubit(
            exp_rabi,
            section_id="qubit_readout_calib_1",
            readout_id="measure",
            acquire_id="acquire",
            reserve_id="drive",
            acquire_handle="calib_1",
            readout_pulse=readout_pulse,
            readout_weights=readout_weighting_function,
            relax_time=relax_time,
            delay_uid='delay_1'
        )
        
        # apply a sequence of pi pulses
        with exp_rabi.sweep(uid="flip_sweeps", parameter=flips_sweep) as flips_count:
            with exp_rabi.section(uid='preparation'):
                exp_rabi.play(signal="drive", pulse=x180, amplitude=1)
                exp_rabi.delay(signal="drive", time=10e-9)
            with exp_rabi.section(uid='preparation_2', play_after='preparation'):
                exp_rabi.play(signal="drive_ef", pulse=x90ef, amplitude=preamp)
                exp_rabi.delay(signal="drive_ef", time=10e-9)

            @repeat(flips_count, exp_rabi)
            def _pi_pulses():
                with exp_rabi.section():
                    exp_rabi.play(signal="drive_ef", pulse=tpulse, amplitude=1)
                    exp_rabi.delay(signal="drive_ef", time=10e-9)

            with exp_rabi.section(uid='delay_ef'):
                exp_rabi.delay(signal="drive_ef", time=10e-9)
            
            with exp_rabi.section(uid='post_flip', play_after='delay_ef'):
                exp_rabi.play(signal="drive", pulse=x180, amplitude=1)
            # readout pulse and data acquisition
            readoutQubit(
                exp_rabi,
                section_id="qubit_readout",
                readout_id="measure",
                acquire_id="acquire",
                reserve_id="drive",
                acquire_handle="q0_rabi",
                readout_pulse=readout_pulse,
                readout_weights=readout_weighting_function,
                play_after_section = 'post_flip',
                relax_time=relax_time,
                delay_uid='delay_2'
            )
    return exp_rabi

# function that returns single shots at single frequency, no drive
def make_readout_single_shot(readout_pulse, readout_weighting_function, relax_time, n_average):
    exp_SS = Experiment(
        uid="Single Shots",
        signals=[
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define Rabi experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_SS.acquire_loop_rt(
        uid="S_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.SINGLE_SHOT,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        # readout pulse and data acquisition
        readoutQubit(
            exp_SS,
            section_id="qubit_readout",
            readout_id="measure",
            acquire_id="acquire",
            acquire_handle="shots",
            readout_pulse=readout_pulse,
            readout_weights=readout_weighting_function,
            relax_time=relax_time,
        )
    return exp_SS

def make_flux_pulse_testing(flux_pulse, n_average, rep_sweep, delay_time = 1e-6, amplitude=1):
    exp_tr_amp = Experiment(
        uid="Th_res_amp",
        signals=[
            ExperimentSignal("th_res"),
            ExperimentSignal("drive"),
            ExperimentSignal("measure"),
            ExperimentSignal("acquire"),
        ],
    )

    ## define Rabi experiment pulse sequence
    # outer loop - real-time, cyclic averaging
    with exp_tr_amp.acquire_loop_rt(
        uid="tr_amp_shots",
        count=pow(2, n_average),
        averaging_mode=AveragingMode.CYCLIC,
        acquisition_type=AcquisitionType.INTEGRATION,
    ):
        with exp_tr_amp.sweep(uid='mock_sweep', parameter=rep_sweep):
            with exp_tr_amp.section(uid="th_res_pulse", alignment=SectionAlignment.RIGHT):
                exp_tr_amp.play(signal="th_res", pulse=flux_pulse, amplitude=amplitude)
                exp_tr_amp.delay(signal="th_res", time=delay_time)
                # exp_tr_amp.delay(signal="drive", time=delay_time)

    return exp_tr_amp

    
# # function that modifies an experiment by adding the qubit readout and signal acquisition sections
# def readoutQubit(
#     exp,
#     section_id="qubit_readout",
#     readout_id="q0_measure",
#     acquire_id="q0_acquire",
#     acquire_handle="q0_acquire",
#     play_after_section=None,
#     reserve_id=None,
#     readout_pulse=readout_pulse,
#     readout_weights=readout_weighting_function,
#     relax_time=10e-6,
# ):
#     # section for readout pulse and data acquisition
#     with exp.section(uid=section_id, play_after = play_after_section):
#         # reserve drive line for duration of readout and data acquisition - if selected
#         if reserve_id is not None:
#             exp.reserve(signal=reserve_id)
#         # play readout pulse on measure line
#         exp.play(signal=readout_id, pulse=readout_pulse)
#         # trigger signal data acquisition
#         exp.acquire(
#             signal=acquire_id,
#             handle=acquire_handle,
#             kernel=readout_weights,
#         )
#     with exp.section(uid="delay", play_after=section_id):
#         # relax time after readout - for qubit relaxation to groundstate and signal processing
#         exp.delay(signal=readout_id, time=relax_time)
#         # make sure that the drive line is reserved also for the relax time, if selected
#         if reserve_id is not None:
#             exp.reserve(signal=reserve_id)