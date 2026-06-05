# 
# This file is a wrapper for three level population measurement data processing
# 
#%config IPCompleter.greedy=True

# convenience import for all QCCS software functionality
#from laboneq.simple import *

# helper import - needed to extract qubit and readout parameters from measurement data
#from helpers.meas_helper_mod import *

#really needed imports
import numpy as np
from scipy.optimize import fsolve

#imports which can be needed
#from scipy.io import savemat, loadmat
#from YokoGS200_wrapper import YokoGS200
import matplotlib.pyplot as plt

#######################################################
#list of population labels
pop_label_list = ['x0', 'x1', 'x2', 'y0', 'y1', 'y2']
################################################
#Simple function to get temperature from pe/pg
def T_calc(C, f_q):
	h = 6.628*1E-2
	k = 1.381
	return -(h*f_q/k)/np.log(C)

def A_temp(T, A, f_q, anharm):
    h = 6.628*1E-2
    k = 1.381
    f_g2 = 2*f_q-anharm
    num = 1-np.exp(-h*f_q/k/T)
    denum = 1-np.exp(-h*f_g2/k/T)
    return A - num/denum

def B_temp(T, B, f_q, anharm):
    h = 6.628*1E-2
    k = 1.381
    f_g2 = 2*f_q-anharm
    num = np.exp(-h*f_q/k/T)-np.exp(-h*f_g2/k/T)
    denum = 1-np.exp(-h*f_q/k/T)
    return B - num/denum

def C_temp(T, C, f_q, anharm):
    h = 6.628*1E-2
    k = 1.381
    f_g2 = 2*f_q-anharm
    num = np.exp(-h*f_q/k/T)-np.exp(-h*f_g2/k/T)
    denum = 1-np.exp(-h*f_g2/k/T)
    return C - num/denum

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
#N.B: if 'three_levels' option disabled, this function use simple way to get temperatures, it works only for low-temperature limit!
def get_temperature(ABC, f_q, anharm, three_levels = False):
    result = {}
    for k in ABC.keys():
        new_k = 'T'+k
        if k[0] == 'A':
            result[new_k] = T_calc(1-ABC[k], f_q)*1e3
            if three_levels:
                for index, x in np.ndenumerate(ABC[k]):
                    result[new_k][index] = fsolve(A_temp, result[new_k][index]*1e-3, args=(x, f_q, anharm))*1e3
        elif k[0] == 'B':
            result[new_k] = T_calc(ABC[k]/(ABC[k]+1), f_q)*1e3
            if three_levels:
                for index, x in np.ndenumerate(ABC[k]):
                    result[new_k][index] = fsolve(B_temp, result[new_k][index]*1e-3, args=(x, f_q, anharm))*1e3 
        elif k[0] == 'C':
            result[new_k] = T_calc(ABC[k], f_q)*1e3
            if three_levels:
                for index, x in np.ndenumerate(ABC[k]):
                    result[new_k][index] = fsolve(C_temp, result[new_k][index]*1e-3, args=(x, f_q, anharm))*1e3
            
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
        stat[k] = np.array([M, V, V/M])
    return stat

#same function as previous but correctly proceeds nan values
def get_stat_nan(data):
    stat = {}
    for k in data.keys():
        M = np.nanmean(data[k])
        V = np.sqrt(np.nanvar(data[k], ddof=1))
        stat[k] = np.array([M, V, V/M])
    return stat

#extract temperatures from populations using axis projections
def make_all_temperatures(pop_full_results, f_q, anharm, phase = 0, three_levels = True):
    proj_I, proj_Q = make_projection(pop_full_results, phase)
    
    ABC_I = get_ABC(proj_I)
    ABC_Q = get_ABC(proj_Q)

    TABC_I = get_temperature(ABC_I, f_q, anharm, three_levels = three_levels)
    TABC_Q = get_temperature(ABC_Q, f_q, anharm, three_levels = three_levels)
    return TABC_I, TABC_Q

#plot temperature data
def plot_temperatures(TABC_I, TABC_Q, skip = [], xlim = None, ylim = None):
    fig, ax = plt.subplots(2, 1, sharex = True, figsize = (10, 8))

    ax[0].set_prop_cycle(color=['red', 'orange', 'gold', 'green', 'limegreen', 'cyan', 'blue', 'darkviolet', 'magenta'])
    ax[1].set_prop_cycle(color=['red', 'orange', 'gold', 'green', 'limegreen', 'cyan', 'blue', 'darkviolet', 'magenta'])


    fig.supxlabel('Point number')
    fig.supylabel('Effective temperature, mK')

    ax[0].set_title('I component')
    ax[1].set_title('Q component')

    for k in TABC_I.keys():
        if k in skip:
            continue
        ax[0].plot(TABC_I[k], 'o-', label = k)
    ax[0].legend()

    for k in TABC_Q.keys():
        if k in skip:
            continue
        ax[1].plot(TABC_Q[k], 'o-', label = k)

    if xlim is not None:
        ax[0].set_xlim(xlim)
        ax[1].set_xlim(xlim)

    if ylim is not None:
        ax[0].set_ylim(ylim)
        ax[1].set_ylim(ylim)

    ax[1].legend()
    
############################################################################################
#alternative way to proceed the data, based on the 'parallel' aproach
def get_diff(pop_proj):
    x0 = pop_proj['x0']
    x1 = pop_proj['x1']
    x2 = pop_proj['x2']
    y0 = pop_proj['y0']
    y1 = pop_proj['y1']
    y2 = pop_proj['y2']
    diff_dict = {}
    #parallel to ge, index1
    diff_dict['x0x1'] = x0-x1 #order1, mid
    diff_dict['y0y1'] = y0-y1 #order1, max
    diff_dict['x2y2'] = x2-y2 #order0, min

    #parallel to gf, index2
    diff_dict['y0x2'] = y0-x2 #order1, mid
    diff_dict['x0y2'] = x0-y2 #order1, max
    diff_dict['x1y1'] = x1-y1 #order0, min

    #parallel to ef, index3
    diff_dict['y1y2'] = y1-y2 #order1, mid
    diff_dict['x1x2'] = x1-x2 #order1, max
    diff_dict['x0y0'] = x0-y0 #order0, min
    return diff_dict

def get_axes_and_rotate(D1, D2, D3):
    # Angle1 = np.mean(np.angle(D1))
    # Angle2 = np.mean(np.angle(D2))

    Angle1 = np.angle(D1)
    Angle2 = np.angle(D2)
    angle = (Angle1+Angle2)/2
    D1_rot = D1*np.exp(-1j*angle)
    D2_rot = D2*np.exp(-1j*angle)
    D3_rot = D3*np.exp(-1j*angle)

    A = D1_rot.real/D2_rot.real
    B = D3_rot.real/D1_rot.real
    C = D3_rot.real/D2_rot.real

    # A = D1_rot.imag/D2_rot.imag
    # B = D3_rot.imag/D1_rot.imag
    # C = D3_rot.imag/D2_rot.imag
    
    return A, B, C

def get_ABC_parallel(pop_full_results):
    diff_dict = get_diff(pop_full_results)
    
    result ={}

    result['A1'], result['B1'], result['C1'] = get_axes_and_rotate(diff_dict['x0x1'], diff_dict['y0y1'], diff_dict['x2y2'])

    result['A2'], result['B2'], result['C2'] = get_axes_and_rotate(diff_dict['y0x2'], diff_dict['x0y2'], diff_dict['x1y1'])

    result['A3'], result['B3'], result['C3'] = get_axes_and_rotate(diff_dict['y1y2'], diff_dict['x1x2'], diff_dict['x0y0'])

    return result

def get_C_from_ABC(ABC_dict):
    CCC_dict = {}
    for k in ABC_dict.keys():
        kn = 'C'+k
        if 'A' in k:
            CCC_dict[kn] = 1-ABC_dict[k]
        elif 'B' in k:
            CCC_dict[kn] = ABC_dict[k]/(1+ABC_dict[k])
        else:
            CCC_dict[kn] = ABC_dict[k]
    return CCC_dict

#plot temperature data
def plot_temp_single(TABC, skip = [], xlim = None, ylim = None, xdata = None, xlabel = 'Point Number'):
    if xdata is not None:
        assert len(xdata) == len(TABC[list(TABC.keys())[0]]), f'Provide xdata array of proper length! Must be {len(TABC[0])}, not {len(xdata)}'
    fig, ax = plt.subplots(1, 1, sharex = True, figsize = (8, 6))

    ax.set_prop_cycle(color=['red', 'orange', 'gold', 'green', 'limegreen', 'cyan', 'blue', 'darkviolet', 'magenta'])

    fig.supxlabel(xlabel)
    fig.supylabel('Effective temperature, mK')

    for k in TABC.keys():
        if k in skip:
            continue
        if xdata is None:
            ax.plot(TABC[k], 'o-', label = k)
        else:
            ax.plot(xdata, TABC[k], 'o-', label = k)
    ax.legend()

    if xlim is not None:
        ax.set_xlim(xlim)

    if ylim is not None:
        ax.set_ylim(ylim)

    return fig, ax

############################################################################################
#rotate complex data, make projections and extract temperatures
def make_rotation_temperature(data, phase_arr, f_q, anharm, three_levels = True):
    STAT_I = {}
    STAT_Q = {}

    for i in range(len(phase_arr)):
        proj_I, proj_Q = make_projection(data, phase_arr[i])
    
        ABC_I = get_ABC(proj_I)
        ABC_Q = get_ABC(proj_Q)

        TABC_I = get_temperature(ABC_I, f_q, anharm, three_levels = three_levels)
        TABC_Q = get_temperature(ABC_Q, f_q, anharm, three_levels = three_levels)

        stat_TABC_I = get_stat(TABC_I)
        stat_TABC_Q = get_stat(TABC_Q)
        for k in stat_TABC_I.keys():
            if i == 0:
                STAT_I[k] = [stat_TABC_I[k]]
                STAT_Q[k] = [stat_TABC_Q[k]]
            else:
                STAT_I[k].append(stat_TABC_I[k])
                STAT_Q[k].append(stat_TABC_Q[k])

    for k in stat_TABC_I.keys():
        STAT_I[k] = np.array(STAT_I[k])
        STAT_Q[k] = np.array(STAT_Q[k])

    return STAT_I, STAT_Q

#plot statictics for previos data
def plot_rotation_stat(phase_arr, STAT_I, STAT_Q, info_type = 'rel_err'):
    if info_type == 'mean':
        it = 0
        title = 'Mean of effective temperature vs. phase rotation'
        ylabel = 'Effective temperature, mK'
    elif info_type == 'error':
        it = 1
        title = 'Absolute errors for effective temperature vs. phase rotation'
        ylabel = 'Absolute error'
    elif info_type == 'rel_err':
        it = 2
        title = 'Relative errors for effective temperature vs. phase rotation'
        ylabel = 'Relative error'

    
    fig, ax = plt.subplots(3, 3, sharex = True, figsize = (10, 8))

    fig.suptitle(title, fontsize=16)

    fig.supylabel(ylabel)
    fig.supxlabel('Phase')

    ax[0,0].plot(phase_arr, STAT_I['TA1'][:,it], label = 'I')
    ax[0,0].plot(phase_arr, STAT_Q['TA1'][:,it], label = 'Q')
    ax[0,1].plot(phase_arr, STAT_I['TA2'][:,it], label = 'I')
    ax[0,1].plot(phase_arr, STAT_Q['TA2'][:,it], label = 'Q')
    ax[0,2].plot(phase_arr, STAT_I['TA3'][:,it], label = 'I')
    ax[0,2].plot(phase_arr, STAT_Q['TA3'][:,it], label = 'Q')

    ax[1,0].plot(phase_arr, STAT_I['TB1'][:,it], label = 'I')
    ax[1,0].plot(phase_arr, STAT_Q['TB1'][:,it], label = 'Q')
    ax[1,1].plot(phase_arr, STAT_I['TB2'][:,it], label = 'I')
    ax[1,1].plot(phase_arr, STAT_Q['TB2'][:,it], label = 'Q')
    ax[1,2].plot(phase_arr, STAT_I['TB3'][:,it], label = 'I')
    ax[1,2].plot(phase_arr, STAT_Q['TB3'][:,it], label = 'Q')

    ax[2,0].plot(phase_arr, STAT_I['TC1'][:,it], label = 'I')
    ax[2,0].plot(phase_arr, STAT_Q['TC1'][:,it], label = 'Q')
    ax[2,1].plot(phase_arr, STAT_I['TC2'][:,it], label = 'I')
    ax[2,1].plot(phase_arr, STAT_Q['TC2'][:,it], label = 'Q')
    ax[2,2].plot(phase_arr, STAT_I['TC3'][:,it], label = 'I')
    ax[2,2].plot(phase_arr, STAT_Q['TC3'][:,it], label = 'Q')

    ax[0,0].set_title('A1')
    ax[1,0].set_title('B1')
    ax[2,0].set_title('C1')
    ax[0,1].set_title('A2')
    ax[1,1].set_title('B2')
    ax[2,1].set_title('C2')
    ax[0,2].set_title('A3')
    ax[1,2].set_title('B3')
    ax[2,2].set_title('C3')

    fig.legend()

#find optimal temperature?
def make_optimal_temperature(data, phase_arr, f_q, anharm, skip = [], info_type = 'rel_err', three_levels = True):
    STAT_I, STAT_Q = make_rotation_temperature(data, phase_arr, f_q, anharm, three_levels = three_levels)

    optimal_method = {'rel_err': 1000,
                     'phase': 0,
                      'ph_p': 0,
                     'method': '0',
                     'axes': '0'
                     }
    if info_type == 'mean':
        it = 0
    elif info_type == 'error':
        it = 1
    elif info_type == 'rel_err':
        it = 2
    
    for k in STAT_I.keys():
        if k in skip:
            continue
        rel_Q = np.nanmin(STAT_Q[k][:,it])
        ph_p_Q = np.nanargmin(STAT_Q[k][:,it])
        rel_I = np.nanmin(STAT_I[k][:,it])
        ph_p_I = np.nanargmin(STAT_I[k][:,it])


        if (rel_I or ph_p_Q) < optimal_method['rel_err']:
            optimal_method['method'] = k
            if abs(phase_arr[ph_p_Q]) < abs(phase_arr[ph_p_I]):
                optimal_method['rel_err'] = rel_Q
                optimal_method['phase'] = phase_arr[ph_p_Q]
                optimal_method['ph_p'] = ph_p_Q
                optimal_method['axes'] = 'Q'
            else:
                optimal_method['rel_err'] = rel_I
                optimal_method['phase'] = phase_arr[ph_p_I]
                optimal_method['ph_p'] = ph_p_I
                optimal_method['axes'] = 'I'
    return optimal_method

def find_optimal_temperature(pop_full_results, optimal_method, f_q, anharm, three_levels = True):
    proj_I, proj_Q = make_projection(pop_full_results, optimal_method['phase'])

    if optimal_method['axes'] == 'I':
        ABC = get_ABC(proj_I)
        TABC = get_temperature(ABC, f_q, anharm, three_levels = three_levels)
    elif optimal_method['axes'] == 'Q':
        ABC = get_ABC(proj_Q)
        TABC = get_temperature(ABC, f_q, anharm, three_levels = three_levels)
    else:
        print('Wrong axe in optimal_parameters!')
        return None
    Teff = TABC[optimal_method['method']]
    return Teff

########################################################################################
def plot_stat(STAT_I, STAT_Q, element = 0):    
    labels = []
    I_mean = []
    Q_mean = []
    I_err = []
    Q_err = []

    for k in STAT_I.keys():
        sh = STAT_I[k].shape
        if len(sh) == 1:
            STAT_I[k] = np.reshape(STAT_I[k], (1,sh[0]))
            STAT_Q[k] = np.reshape(STAT_Q[k], (1,sh[0]))
        
        labels.append(k)
        I_mean.append(STAT_I[k][element,0])
        Q_mean.append(STAT_Q[k][element,0])
        I_err.append(STAT_I[k][element,1])
        Q_err.append(STAT_Q[k][element,1])

    fig, ax = plt.subplots(1, 2, sharex = True, figsize = (10, 8))

    fig.supylabel('Effective temperature, mK')

    ax[0].set_title('I component')
    ax[1].set_title('Q component')

    ax[0].bar(labels, I_mean)
    ax[0].errorbar(labels, I_mean, yerr=I_err, fmt="o", color="r")

    ax[1].bar(labels, Q_mean)
    ax[1].errorbar(labels, Q_mean, yerr=Q_err, fmt="o", color="r")
    
#######################################################################################