# 
# This file is a wrapper for qubit measurements
# Here are make_ functions for the main experiments
#
#%config IPCompleter.greedy=True

# convenience import for all QCCS software functionality
from laboneq.simple import *

# helper import - needed to extract qubit and readout parameters from measurement data
# from lib.helpers.meas_helper_mod_2 import *
from lib.helpers.meas_helper_mod import *

#really needed imports
import numpy as np

#imports which can be needed
#from scipy.io import savemat, loadmat
#from YokoGS200_wrapper import YokoGS200
import matplotlib.pyplot as plt

#######################################################################################################
# function that returns an amplitude Rabi experiment, set map, calibration and  
def create_rabi(rabi_sweep, gaussian_pulse, readout, n_average):
    exp_rabi = make_rabi(rabi_sweep, 
                         gaussian_pulse, 
                         readout['readout_pulse'], 
                         readout['readout_weighting_function'], 
                         readout['relax_time'], 
                         n_average)
    
    exp_rabi.set_calibration(readout_calib(readout))
    exp_rabi.set_signal_map(qubit_meas_map)
    
    return exp_rabi

# function that returns single shot Rabi experiment
def create_rabi_SS(rabi_sweep, gaussian_pulse, readout, n_average):
    exp_rabi_SS = make_rabi_SS(rabi_sweep, 
                         gaussian_pulse, 
                         readout['readout_pulse'], 
                         readout['readout_weighting_function'], 
                         readout['relax_time'], 
                         n_average)
    
    exp_rabi_SS.set_calibration(readout_calib(readout))
    exp_rabi_SS.set_signal_map(qubit_meas_map)
    
    return exp_rabi_SS

# function that returns single shot experiment
def create_SS(state, x_180, x_180_ef, readout, n_average):
    exp_SS = make_shots(state, 
                        x_180,
                        x_180_ef,
                        readout['readout_pulse'], 
                        readout['readout_weighting_function'], 
                        readout['relax_time'], 
                        n_average)
    
    exp_SS.set_calibration(readout_calib(readout))
    exp_SS.set_signal_map(qubit_ef_map)
    
    return exp_SS

# function that returns an amplitude Rabi experiment for ef-levels with ONE ge pulse (prepulse)
def create_rabi_ef(rabi_ef_sweep, gaussian_pulse, readout, n_average, x180, ge_amp = 0.0, n_ge_pulses = 1):   
    if n_ge_pulses == 1:
        exp_rabi_ef = make_rabi_ef_1(rabi_ef_sweep, 
                                       gaussian_pulse, 
                                       readout['readout_pulse'], 
                                       readout['readout_weighting_function'], 
                                       readout['relax_time'], 
                                       n_average, 
                                       x180, 
                                       ge_amp = ge_amp)
    elif n_ge_pulses == 2:
        exp_rabi_ef = make_rabi_ef_2(rabi_ef_sweep, 
                                       gaussian_pulse, 
                                       readout['readout_pulse'], 
                                       readout['readout_weighting_function'], 
                                       readout['relax_time'], 
                                       n_average, 
                                       x180, 
                                       ge_amp = ge_amp)
    else:
        print('Wrong number of ge_pulses: could be only 1 or 2.')
    
    exp_rabi_ef.set_calibration(readout_calib(readout))
    exp_rabi_ef.set_signal_map(qubit_ef_map)
    
    return exp_rabi_ef


# function that returns a T1-measurement experiment
def create_t1(t1_sweep, x180, readout, n_average):
    exp_t1 = make_t1(t1_sweep, 
                     x180, 
                     readout['readout_pulse'], 
                     readout['readout_weighting_function'], 
                     readout['relax_time'], 
                     n_average)
    
    exp_t1.set_calibration(readout_calib(readout))
    exp_t1.set_signal_map(qubit_meas_map)
    
    return exp_t1


# function that returns a T1-measurement experiment for ef-level with ONE ge-prepulse
def create_T1_ef_1(t1_ef_sweep, x180_ef, readout, n_average, x180, ge_amp = 0.0):
    exp_t1_ef = make_T1_ef_1(t1_ef_sweep, 
                             x180_ef, 
                             readout['readout_pulse'], 
                             readout['readout_weighting_function'], 
                             readout['relax_time'], 
                             n_average, 
                             x180, 
                             ge_amp = ge_amp)
    
    exp_t1_ef.set_calibration(readout_calib(readout))
    exp_t1_ef.set_signal_map(qubit_ef_map)
    
    return exp_t1_ef 


# function that returns a Ramsey experiment
def create_ramsey(ramsey_sweep, x90, readout, n_average, parameters):
    
    exp_ramsey = make_ramsey(ramsey_sweep, 
                             x90, 
                             readout['readout_pulse'], 
                             readout['readout_weighting_function'], 
                             readout['relax_time'], 
                             n_average)
    
    ramsey_cal = make_ramsey_calib(parameters["qb_freq"], parameters["ramsey_det"])
    exp_ramsey.set_calibration(ramsey_cal)
    exp_ramsey.set_calibration(readout_calib(readout))
    exp_ramsey.set_signal_map(qubit_meas_map)
    
    return exp_ramsey


# function that returns a Ramsey experiment on ef-transition with TWO ge pulses
def create_ramsey_ef(ramsey_ef_sweep, x90_ef, readout, n_average, x180, parameters, ge_amp = 0.0):
    
    exp_ramsey_ef = make_ramsey_ef_2(ramsey_ef_sweep, 
                                     x90_ef, 
                                     readout['readout_pulse'], 
                                     readout['readout_weighting_function'], 
                                     readout['relax_time'], 
                                     n_average,
                                     x180,
                                     ge_amp = ge_amp)
    
    ramsey_ef_cal = make_ramsey_ef_calib(parameters["qb_ef_freq"], parameters["ramsey_det_ef"])
    exp_ramsey_ef.set_calibration(ramsey_ef_cal)
    exp_ramsey_ef.set_calibration(readout_calib(readout))
    exp_ramsey_ef.set_signal_map(qubit_ef_map)
    
    return exp_ramsey_ef
    

# function that returns a Hahn-echo experiment
def create_echo(echo_sweep, x90, x180, readout, n_average):
    
    exp_echo = make_echo(echo_sweep, 
                         x90,
                         x180, 
                         readout['readout_pulse'], 
                         readout['readout_weighting_function'], 
                         readout['relax_time'], 
                         n_average)
    
    exp_echo.set_calibration(readout_calib(readout))
    exp_echo.set_signal_map(qubit_meas_map)

    
    return exp_echo
    

########################################################################################################
#Create population measurement experiment

#function that return full population experiment
def create_exp_population_full(x180, x180_ef, readout, n_average):
    #make experiment
    exp_population_full = make_exp_population_full(x180, 
                                                   x180_ef, 
                                                   readout['readout_pulse'], 
                                                   readout['readout_weighting_function'], 
                                                   readout['relax_time'], 
                                                   n_average)
    #set calibration and signal map
    exp_population_full.set_calibration(readout_calib(readout))
    exp_population_full.set_signal_map(qubit_ef_map)

    
    return exp_population_full

def create_exp_population_flux(x180, x180_ef, flux_pulse, readout, n_average):
    #make experiment
    exp_population_flux = make_exp_population_flux(x180, 
                                                   x180_ef, 
                                                   flux_pulse,
                                                   readout['readout_pulse'], 
                                                   readout['readout_weighting_function'], 
                                                   readout['relax_time'], 
                                                   n_average)
    #set calibration and signal map
    exp_population_flux.set_calibration(readout_calib(readout))
    exp_population_flux.set_signal_map(qubit_all_map)

    
    return exp_population_flux

     

def create_exp_population_correlations(x180, r_delay, readout, n_average):
    #make experiment
    exp_pop_corr = make_exp_pop_correlations(x180, 
                                             r_delay,
                                            readout['readout_pulse'], 
                                            readout['readout_weighting_function'], 
                                            readout['relax_time'], 
                                            n_average)
    #set calibration and signal map
    exp_pop_corr.set_calibration(readout_calib(readout))
    exp_pop_corr.set_signal_map(qubit_meas_map)

    
    return exp_pop_corr


############################################################################################################

# function that defines a qubit spectroscopy experiment, and takes the frequency sweep as a parameter
def create_qubit_spec(freq_sweep_TT, square_pulse, readout, n_average):
    exp_qspec = qubit_spectroscopy(freq_sweep_TT, 
                                   square_pulse, 
                                   readout['readout_pulse'], 
                                   readout['readout_weighting_function'], 
                                   readout['relax_time'], 
                                   n_average)
    exp_qspec.set_calibration(qubit_spec_calib(freq_sweep_TT))
    exp_qspec.set_calibration(readout_calib(readout))
    exp_qspec.set_signal_map(qubit_meas_map)
    
    return exp_qspec


# function that returns a qubit spectroscopy experiment- accepts frequency sweep range as parameter
def create_qubit_ef_spec(freq_sweep_ef, square_pulse, readout, n_average):
    
    exp_ef_qspec = qubit_ef_spectroscopy(freq_sweep_ef, 
                                         square_pulse, 
                                         readout['readout_pulse'], 
                                         readout['readout_weighting_function'], 
                                         readout['relax_time'], 
                                         n_average)
    exp_ef_qspec.set_calibration(qubit_ef_spec_calib(freq_sweep_ef))
    exp_ef_qspec.set_calibration(readout_calib(readout))
    exp_ef_qspec.set_signal_map(qubit_ef_only_map)

    
    return exp_ef_qspec

def create_qubit_ef_spec_prep(freq_sweep_ef, x180, square_pulse, readout, n_average):
    
    exp_ef_qspec = qubit_ef_spectroscopy_with_prepulse(freq_sweep_ef,
                                                       x180,
                                                       square_pulse, 
                                                       readout['readout_pulse'], 
                                                       readout['readout_weighting_function'], 
                                                       readout['relax_time'], 
                                                       n_average)
    exp_ef_qspec.set_calibration(qubit_ef_spec_calib(freq_sweep_ef))
    exp_ef_qspec.set_calibration(readout_calib(readout))
    exp_ef_qspec.set_signal_map(qubit_ef_map)

    
    return exp_ef_qspec
##########################################################################################   
# create resonator spectroscopy experiment with/without highter levels pumping 
def create_res_spec_gef(freq_sweep, x180, x180_ef, readout, n_average, level = 0):  
    res_spec_gef_calib = res_spec_calib(freq_sweep)
    
    if level == 0:
        exp_spec = make_res_spec_e(freq_sweep, 
                                   x180, 
                                   readout['readout_pulse'], 
                                   readout['readout_weighting_function'], 
                                   readout['relax_time'], 
                                   n_average,  
                                   0.0)
        exp_spec.set_calibration(res_spec_gef_calib)
        #exp_spec.set_calibration(readout_calib(readout))
        exp_spec.set_signal_map(qubit_meas_map)
    elif level == 1:
        exp_spec = make_res_spec_e(freq_sweep, 
                                   x180, 
                                   readout['readout_pulse'], 
                                   readout['readout_weighting_function'], 
                                   readout['relax_time'], 
                                   n_average, 
                                   ge_amp = 1.0)
        exp_spec.set_calibration(res_spec_gef_calib)
        #exp_spec.set_calibration(readout_calib(readout))
        exp_spec.set_signal_map(qubit_meas_map)
    elif level == 2:
        exp_spec = make_res_spec_f(freq_sweep, 
                                   x180,
                                   x180_ef,
                                   readout['readout_pulse'], 
                                   readout['readout_weighting_function'], 
                                   readout['relax_time'], 
                                   n_average)
        exp_spec.set_calibration(res_spec_gef_calib)
        #exp_spec.set_calibration(readout_calib(readout))
        exp_spec.set_signal_map(qubit_ef_map)
    else:
        print('Wrong level number: could be only 0, 1 or 2.')
    
    return exp_spec

# def create_res_spec_flux(freq_sweep, x180, x180_ef, readout, n_average, level = 0):  
#     res_spec_gef_calib = res_spec_calib(freq_sweep)
    
#     exp_spec = make_res_spec_flux(freq_sweep,
#                                   flux_pulse
#                                   x180, 
#                                   readout['readout_pulse'], 
#                                   readout['readout_weighting_function'], 
#                                   readout['relax_time'], 
#                                   n_average,  
#                                   0.0)
#     exp_spec.set_calibration(res_spec_gef_calib)
#     #exp_spec.set_calibration(readout_calib(readout))
#     exp_spec.set_signal_map(qubit_resonator_map)

    
#     return exp_spec
# ##########################################################################################   
# propagation delay experiment

def create_prop_delay(delay_sweep, readout_pulse, acquire_length, relax_time, n_average):
    exp = make_propagation_delay(delay_sweep, readout_pulse, acquire_length, relax_time, n_average)
    exp.set_signal_map(MA_map) 

    return exp

############################
# rabi error amplification
def create_rabi_error_amp(flips_sweep, x180, x90, readout, n_average, target_pulse):
    exp = make_rabi_error_amplification(flips_sweep, x180, x90, 
                                        readout['readout_pulse'], 
                                        readout['readout_weighting_function'],
                                        readout['relax_time'],
                                        n_average,
                                       target_pulse)

    exp.set_calibration(readout_calib(readout))
    exp.set_signal_map(qubit_meas_map)

    return exp

# rabi error amplification
def create_rabi_error_amp_ef(flips_sweep, x180, x90, x180ef, x90ef, readout, n_average, target_pulse):
    exp = make_rabi_error_amplification_ef(flips_sweep, x180, x90, x180ef, x90ef,
                                        readout['readout_pulse'], 
                                        readout['readout_weighting_function'],
                                        readout['relax_time'],
                                        n_average,
                                       target_pulse)

    exp.set_calibration(readout_calib(readout))
    exp.set_signal_map(qubit_ef_map)

    return exp


def create_readout_single_shot(readout, n_average):
    exp = make_readout_single_shot(readout_pulse=readout['readout_pulse'], 
                                   readout_weighting_function=readout['readout_weighting_function'], 
                                   relax_time=readout['relax_time'], 
                                   n_average=n_average)

    exp.set_calibration(readout_calib(readout))
    exp.set_signal_map(MA_map)

    return exp