# 
# This file is a wrapper for qubit measurements
# Here are make_ functions for the main experiments
#
#%config IPCompleter.greedy=True

# convenience import for all QCCS software functionality
from laboneq.simple import *

# helper import - needed to extract qubit and readout parameters from measurement data
from helpers.meas_helper_mod import *

#really needed imports
import numpy as np

#imports which can be needed
#from scipy.io import savemat, loadmat
#from YokoGS200_wrapper import YokoGS200
import matplotlib.pyplot as plt

################################################
#Simple function to get temperature from pe/pg
def T_calc(C, f_q):
	h = 6.628*1E-2
	k = 1.381
	return -(h*f_q/k)/np.log(C)

###############################################
#Function to get 9 ABC parameters from dict with projected data
def get_ABC(pop_proj):
    x0 = pop_proj['x0']
    x1 = pop_proj['x1']
    x2 = pop_proj['x2']
    y0 = pop_proj['y0']
    y1 = pop_proj['y1']
    y2 = pop_proj['y2']

    result ={}
    result['A1'] = (x0-x1)/(y0-y1)
    result['B1'] = (x2-y2)/(x0-x1)
    result['C1'] = result['A1']*result['B1']

    result['A2'] = (y0-x2)/(x0-y2)
    result['B2'] = (x1-y1)/(y0-x2)
    result['C2'] = result['A2']*result['B2']

    result['A3'] = (y1-y2)/(x1-x2)
    result['B3'] = (x0-y0)/(y1-y2)
    result['C3'] = result['A3']*result['B3']

    return result

#Function to rotate and project complex measurement results to two ortoganal axes
def make_projection(pop_full_results, phase):
    res_I = {}
    res_Q = {}
    keys = pop_full_results.keys() 
    for k in keys:
        rot = pop_full_results[k]*np.exp(1j*phase)
        res_I[k] = rot.real
        res_Q[k] = rot.imag

    return res_I, res_Q

#Function to make temperature from ABC
#N.B: this function use simple way to get temperatures, it works only for low-temperature limit!
def get_temperature(ABC, f_q):
    result = {}
    for k in ABC.keys():
        new_k = 'T'+k
        if k[0] == 'A':
            result[new_k] = T_calc(1-ABC[k], f_q)*1e3
        elif k[0] == 'B':
            result[new_k] = T_calc(ABC[k]/(ABC[k]+1), f_q)*1e3
        elif k[0] == 'C':
            result[new_k] = T_calc(ABC[k], f_q)*1e3
        else:
            print('Wrong key in ABC dictionary!')
    return result

#Function to get statistics: mean value, standart diviation (squre root from shifted variance) and relative error
#return the dictionary with the same keys as in 'data', contain the array for each key, in array [0] - mean, [1] - STD, [2] - rel.error
def get_stat(data):
    stat = {}
    for k in data.keys():
        M = np.mean(data[k])
        V = np.sqrt(np.var(data[k], ddof=1))
        stat[k] = [M, V, V/M]
    return stat