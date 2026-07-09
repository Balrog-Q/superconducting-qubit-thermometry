###
# Simple Qubit class for simplifying device setup calibration
###

from laboneq.simple import *
from copy import deepcopy


# def flatten(l):
#     return [item for sublist in l for item in sublist]


# def get_qubit_parameters(base_parameters, id):
#     parameters = deepcopy(base_parameters)
#     parameters["frequency"] = base_parameters["frequency"][id]
#     parameters["readout_frequency"] = base_parameters["readout_frequency"][id]
#     parameters["drive_lo_frequency"] = base_parameters["drive_lo_frequency"][id // 2]

#     return parameters


# class QubitParameters:
#     def __init__(self, my_parameter_dict):
#         for key in my_parameter_dict.keys():
#             setattr(self, key, my_parameter_dict[key])


# class QubitPulses:
#     def __init__(self, id, parameters: QubitParameters):
#         self.qubit_x90 = pulse_library.drag(
#             uid=f"x90_q{id}",
#             length=parameters.pulse_length,
#             amplitude=parameters.pi_2_amplitude,
#             sigma=0.3,
#             beta=0.4,
#         )
#         self.qubit_x180 = pulse_library.drag(
#             uid=f"x180_q{id}",
#             length=parameters.pulse_length,
#             amplitude=parameters.pi_amplitude,
#             sigma=0.3,
#             beta=0.4,
#         )
#         self.readout_pulse = pulse_library.const(
#             uid=f"readout_pulse_q{id}",
#             length=parameters.readout_length,
#             amplitude=parameters.readout_amplitude,
#         )
#         self.readout_weights = pulse_library.const(
#             uid=f"readout_weights_q{id}",
#             length=parameters.readout_length,
#             amplitude=1,
#         )


# class Qubit:
#     def __init__(self, id, parameter_dict):
#         self.id = id

#         self.parameters = QubitParameters(parameter_dict)

#         self.pulses = QubitPulses(self.id, self.parameters)

#######################################################################################################
#defoult descriptor for SHFQC measurements
my_descriptor=f"""\
instruments:
  SHFQC:
  - address: DEV12192
    uid: device_shfqc
connections:
  device_shfqc:
    - iq_signal: q0/drive
      ports: SGCHANNELS/0/OUTPUT
    - iq_signal: q0/drive_ef
      ports: SGCHANNELS/0/OUTPUT
    - iq_signal: q0/th_res
      ports: SGCHANNELS/1/OUTPUT
    - iq_signal: q0/measure
      ports: [QACHANNELS/0/OUTPUT]
    - acquire_signal: q0/acquire
      ports: [QACHANNELS/0/INPUT]
"""


#######################################################################################################
# function that defines a setup calibration containing the qubit / readout parameters 
def define_calibration(parameters, lo_settings):

     # the calibration object will later be applied to the device setup
    my_calibration = Calibration()
    
    # qubit drive line
    my_calibration["/logical_signal_groups/q0/drive"] = \
        SignalCalibration(
            # each logical signal can have an oscillator associated with it
            oscillator=Oscillator(
                "q0_drive_osc",
                frequency=parameters['qb_freq'],      # IF signal, +/- 500 MHz range
                modulation_type=ModulationType.HARDWARE
            ),
            local_oscillator=Oscillator(
                frequency=lo_settings['qb_lo'],        # LO signal, 4-8 GHz range
            ),
            range=5
        )

    # qubit drive ef line
    my_calibration["/logical_signal_groups/q0/drive_ef"] = \
        SignalCalibration(
            # each logical signal can have an oscillator associated with it
            oscillator=Oscillator(
                "q0_drive_ef_osc",
                frequency=parameters['qb_freq']-parameters['qb_anharm'],      # IF signal, +/- 500 MHz range
                modulation_type=ModulationType.HARDWARE
            ),
            local_oscillator=Oscillator(
                frequency=lo_settings['qb_lo'],        # LO signal, 4-8 GHz range
            ),
            range=5
        )
    
    # thermal resonator line
    my_calibration["/logical_signal_groups/q0/th_res"] = \
        SignalCalibration(
            # each logical signal can have an oscillator associated with it
            oscillator=Oscillator(
                "q0_th_res_osc",
                frequency=parameters['th_res_freq'],      # IF signal, +/- 500 MHz range
                modulation_type=ModulationType.HARDWARE
            ),
            local_oscillator=Oscillator(
                frequency=lo_settings['qb_lo'],        # LO signal, 4-8 GHz range
            ),
            range=5
        )
    
    # readout drive line
    my_calibration["/logical_signal_groups/q0/measure"] = \
         SignalCalibration(
            oscillator=Oscillator(
                "q0_measure_osc",
                frequency=parameters['ro_freq'],
                modulation_type=ModulationType.SOFTWARE
            ),
            port_delay=parameters['ro_delay'],
            local_oscillator=Oscillator(
                frequency=lo_settings['ro_lo'],
            ),
           range=-25
       )
    # acquisition line
    my_calibration["/logical_signal_groups/q0/acquire"] = \
         SignalCalibration(
            oscillator=Oscillator(
                "q0_acquire_osc",
                frequency=parameters['ro_freq'],
                modulation_type=ModulationType.SOFTWARE
            ),
            # add an offset between the readout pulse and the start of the data acquisition - to compensate for round-trip time of readout pulse 
            port_delay=parameters['ro_delay'] + parameters['ro_int_delay'],
            local_oscillator=Oscillator(
                frequency=lo_settings['ro_lo'],
            ),
            range=-30
        )
  
    return my_calibration