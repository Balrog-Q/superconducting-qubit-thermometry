# 
# This file is a wrapper for qubit measurements
#
%config IPCompleter.greedy=True

# convenience import for all QCCS software functionality
from laboneq.simple import *

# helper import - needed to extract qubit and readout parameters from measurement data
from tuneup_helper import *

import numpy as np
from YokoGS200_wrapper import YokoGS200
import matplotlib.pyplot as plt

# function that defines a resonator spectroscopy experiment, and takes the frequency sweep as a parameter
def res_spectroscopy(freq_sweep):
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
                    length=qubit_parameters["ro_len_spec"],
                )
            with exp_spec.section(uid="delay", play_after="spectroscopy"):
                # holdoff time after signal acquisition - minimum 1us required for data processing on UHFQA
                exp_spec.delay(signal="measure", time=1e-6)

    return exp_spec


# function that modifies an experiment by adding the qubit readout and signal acquisition sections
def readoutQubit(
    exp,
    section_id="qubit_readout",
    readout_id="q0_measure",
    acquire_id="q0_acquire",
    acquire_handle="q0_acquire",
    play_after_section=None,
    reserve_id=None,
    readout_pulse=readout_pulse,
    readout_weights=readout_weighting_function,
    relax_time=10e-6,
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
        )
    with exp.section(uid="delay", play_after=section_id):
        # relax time after readout - for qubit relaxation to groundstate and signal processing
        exp.delay(signal=readout_id, time=relax_time)
        # make sure that the drive line is reserved also for the relax time, if selected
        if reserve_id is not None:
            exp.reserve(signal=reserve_id)