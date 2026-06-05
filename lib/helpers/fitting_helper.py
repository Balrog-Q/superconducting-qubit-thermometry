# additional imports for plotting
import matplotlib.pyplot as plt
from matplotlib import cycler
import matplotlib.style as style
import matplotlib.cm as cm

# numpy for mathematics
import numpy as np

# scipy optimize for curve fitting
import scipy.optimize as opt
from scipy import fft

from sklearn.decomposition import PCA

import re
from numpy.typing import NDArray


######################################################################################################
#plot_presets

style.use("default")


plt.rcParams.update(
    {
        "font.weight": "light",
        "axes.labelweight": "light",
        "axes.titleweight": "normal",
        "axes.prop_cycle": cycler(color=["#006699", "#FF0000", "#66CC33", "#CC3399"]),
        "svg.fonttype": "none",  # Make text editable in SVG
        "text.usetex": False,
    }
)

# 2D plot
def plot_result_2d(results, handle, mult_axis=None):
    plt.figure()
    acquired_data = results.get_data(handle)
    if mult_axis is None:
        axis_grid = results.get_axis(handle)[0]
        axis_name = results.get_axis_name(handle)[0]
    else:
        axis_grid = results.get_axis(handle)[0][mult_axis]
        axis_name = results.get_axis_name(handle)[0][mult_axis]

    plt.plot(axis_grid, np.absolute(acquired_data))
    plt.xlabel(axis_name)
    plt.ylabel(handle)


# 3D plot
def plot_result_3d(results, handle):
    plt.figure()
    acquired_data = results.get_data(handle)
    y_axis_grid = results.get_axis(handle)[0]
    y_axis_name = results.get_axis_name(handle)[0]
    x_axis_grid = results.get_axis(handle)[1]
    x_axis_name = results.get_axis_name(handle)[1]

    X, Y = np.meshgrid(x_axis_grid, y_axis_grid)

    ax = plt.axes(projection="3d")
    ax.plot_wireframe(X, Y, np.absolute(acquired_data))
    ax.set_xlabel(x_axis_name)
    ax.set_ylabel(y_axis_name)
    ax.set_zlabel(handle)

    plt.figure()  # Create new dummy figure to ensure no side effects of the current 3D figure


def plot2d_abs(results, handle):
    data = results.get_data(handle)
    axis = results.get_axis(handle)[0]
    xlabel = results.get_axis_name(handle)[0]
    plt.plot(axis, np.abs(data))
    plt.xlabel(xlabel)
    plt.ylabel("level")


############################################################################################
## Definitions for fitting experimental data
def func_lin(x, a, b):
    return a * x + b

def func_parabola(x, a, b, c):
    return a*x**2+b*x+c

# oscillations - Rabi
def func_osc(x, freq, phase, amp=1, off=0):
    return amp * np.cos(freq * x + phase) + off

# decaying oscillations - Ramsey
def func_decayOsc(x, freq, phase, rate, amp=1, off=-0.5):
    return amp * np.cos(freq * x + phase) * np.exp(-rate * x) + off

def func_double_decayOsc_2amps(x, freq, dfreq, phase, rate, amp=1, amp2 = 0.1, off=-0.5):
    return amp * (np.cos(2*np.pi*freq * x + phase) + amp2*np.cos(2*np.pi*(freq + dfreq) * x + phase) )* np.exp(-rate * x) + off

# decaying exponent - T1
def func_exp(x, rate, off, amp=1):
    return amp * np.exp(-rate * x) + off

# two decaying exponents
def func_two_exp(x, rate1, rate2, off, A, B):
    return A * np.exp(-rate1 * x)+ B*np.exp(-rate2 * x) + off

# Lorentzian
def func_lorentz(x, width, pos, amp, off):
    return off + amp * width / (width**2 + (x - pos) ** 2)

# inverted Lorentzian - spectroscopy
def func_invLorentz(x, width, pos, amp, off=1):
    return off - amp * width / (width**2 + (x - pos) ** 2)

# Fano lineshape - spectroscopy
def func_Fano(x, width, pos, amp, fano=0, off=0.5):
    return off + amp * (fano * width + x - pos) ** 2 / (width**2 + (x - pos) ** 2)

def gauss(x, mu, sigma, A):
    return A*np.exp(-(x-mu)**2/2/sigma**2)

def bimodal(x, mu1, sigma1, A1, mu2, sigma2, A2):
    return gauss(x,mu1,sigma1,A1)+gauss(x,mu2,sigma2,A2)

#####################################################################################
def fit_linear(x, y, plot=False):
    """Function to fit linear dependances
    
    """
    popt, pcov = opt.curve_fit(func_lin, x, y)
    
    if plot:
        plt.plot(x, y, ".k")
        plt.plot(x, func_lin(x, *popt), "-r")
        plt.show()

    return popt, pcov

def fit_Rabi(x, y, freq, phase, amp=None, off=None, plot=False, bounds=None):
    """Function to fit Rabi oscillations
    
    """
    if amp is not None:
        if off is not None:
            if bounds is None:
                popt, pcov = opt.curve_fit(func_osc, x, y, p0=[freq, phase, amp, off])
            else:
                popt, pcov = opt.curve_fit(
                    func_osc, x, y, p0=[freq, phase, amp, off], bounds=bounds
                )
        else:
            if bounds is None:
                popt, pcov = opt.curve_fit(func_osc, x, y, p0=[freq, phase, amp])
            else:
                popt, pcov = opt.curve_fit(
                    func_osc, x, y, p0=[freq, phase, amp], bounds=bounds
                )
    else:
        if bounds is None:
            popt, pcov = opt.curve_fit(func_osc, x, y, p0=[freq, phase])
        else:
            popt, pcov = opt.curve_fit(func_osc, x, y, p0=[freq, phase], bounds=bounds)

    if plot:
        plt.plot(x, y, ".k")
        plt.plot(x, func_osc(x, *popt), "-r")
        plt.ylabel('Signal, a.u.')
        plt.ylabel('Amplitude, a.u.')
        plt.show()

    return popt, pcov

def fit_osc_fixed_amp_phase(x, y, freq, fixed_phase, fixed_amp, off=None):
    popt, pcov = opt.curve_fit(lambda x, f, off: func_osc(x, f, fixed_phase, fixed_amp, off), x, y, p0=[freq, off])
    return popt, pcov

def fit_Ramsey(x, y, freq, phase, rate, amp=None, off=None, plot=False, bounds=None):
    """Function to fit Ramsey oscillations
    
    """
    if amp is not None:
        if off is not None:
            if bounds is None:
                popt, pcov = opt.curve_fit(
                    func_decayOsc, x, y, p0=[freq, phase, rate, amp, off]
                )
            else:
                popt, pcov = opt.curve_fit(
                    func_decayOsc, x, y, p0=[freq, phase, rate, amp, off], bounds=bounds
                )
        else:
            if bounds is None:
                popt, pcov = opt.curve_fit(
                    func_decayOsc, x, y, p0=[freq, phase, rate, amp]
                )
            else:
                popt, pcov = opt.curve_fit(
                    func_decayOsc, x, y, p0=[freq, phase, rate, amp], bounds=bounds
                )
    else:
        if bounds is None:
            popt, pcov = opt.curve_fit(func_decayOsc, x, y, p0=[freq, phase, rate])
        else:
            popt, pcov = opt.curve_fit(
                func_decayOsc, x, y, p0=[freq, phase, rate], bounds=bounds
            )

    if plot:
        plt.plot(x, y, ".k")
        plt.plot(x, func_decayOsc(x, *popt), "-r")
        plt.ylabel('Signal, a.u.')
        plt.ylabel('Delay, s')
        plt.show()

    return popt, pcov

def fit_double_Ramsey_2amps(time, trace, 
               freq = 4e6, dfreq = 1e6, phase = np.pi, rate = 1e6, amp = 1e-3, amp2 = 0.1, off = 1e-3, 
               plot = False, 
               bounds = None, zero_ind = 0):
    I_0 = np.real(trace[zero_ind])
    Q_0 = np.imag(trace[zero_ind])
    new_trace = np.sqrt((np.real(trace) - I_0)**2 + (np.imag(trace) - Q_0)**2)
    if amp is not None:
        if off is not None:
            if bounds is None:
                popt, pcov = opt.curve_fit(
                    func_double_decayOsc_2amps, time, new_trace, 
                    p0=[freq, dfreq, phase, rate, amp, amp2, off]
                )
            else:
                popt, pcov = opt.curve_fit(
                    func_double_decayOsc_2amps, time, new_trace, 
                    p0=[freq, dfreq, phase, rate, amp, amp2, off],
                    bounds=bounds
                )
        else:
            if bounds is None:
                popt, pcov = opt.curve_fit(
                    func_double_decayOsc_2amps, time, new_trace, 
                    p0=[freq, dfreq, phase, rate, amp, amp2]
                )
            else:
                popt, pcov = opt.curve_fit(
                    func_double_decayOsc_2amps, time, new_trace,
                    p0=[freq, dfreq, phase, rate, amp, amp2], 
                    bounds=bounds
                )
    else:
        if bounds is None:
            popt, pcov = opt.curve_fit(func_double_decayOsc_2amps, time, new_trace,
                                       p0=[freq, dfreq, phase, rate])
        else:
            popt, pcov = opt.curve_fit(
                func_double_decayOsc_2amps, time, new_trace,
                p0=[freq, dfreq, phase, rate], 
                bounds=bounds
            )
 
    if plot:
        fit_time = np.linspace(time[0], time[-1], 5*len(time))
        plt.plot(time, new_trace, ".k")
        plt.plot(fit_time, func_double_decayOsc_2amps(fit_time, *popt), "-r")
        plt.show()
 
    return popt, pcov

def fit_T1(x, y, rate, off, amp=None, plot=False, bounds=None):
    """Function to fit T1 decay
    
    """
    if bounds is None:
        if amp is None:
            popt, pcov = opt.curve_fit(func_exp, x, y, p0=[rate, off])
        else:
            popt, pcov = opt.curve_fit(func_exp, x, y, p0=[rate, off, amp])
    else:
        if amp is None:
            popt, pcov = opt.curve_fit(func_exp, x, y, p0=[rate, off], bounds=bounds)
        else:
            popt, pcov = opt.curve_fit(
                func_exp, x, y, p0=[rate, off, amp], bounds=bounds
            )

    if plot:
        plt.plot(x, y, ".k")
        plt.plot(x, func_exp(x, *popt), "-r")
        plt.ylabel('Signal, a.u.')
        plt.xlabel('Delay, s')
        #plt.show()

    return popt, pcov

def fit_T1_ef(x, y, rate1, rate2, off, A = 0.1, B = 0.1, plot=False, bounds=None):
    """Function to fit T1 decay for ef level
    
    """
    p0 = [rate1, rate2, off, A, B]
    
    if bounds is None:
        popt, pcov = opt.curve_fit(func_two_exp, x, y, p0=p0)
    else:
        popt, pcov = opt.curve_fit(func_two_exp, x, y, p0=p0, bounds=bounds)

    if plot:
        plt.plot(x, y, ".k")
        plt.plot(x, func_two_exp(x, *popt), "-r")
        plt.ylabel('Signal, a.u.')
        plt.ylabel('Delay, s')
        plt.show()

    return popt, pcov


## function to fit spectroscopy traces
def fit_Spec(x, y, width, pos, amp, off=None, plot=False, bounds=None):
    if off is not None:
        if bounds is None:
            popt, pcov = opt.curve_fit(func_invLorentz, x, y, p0=[width, pos, amp, off])
        else:
            popt, pcov = opt.curve_fit(
                func_invLorentz, x, y, p0=[width, pos, amp, off], bounds=bounds
            )
    else:
        if bounds is None:
            popt, pcov = opt.curve_fit(func_invLorentz, x, y, p0=[width, pos, amp])
        else:
            popt, pcov = opt.curve_fit(
                func_invLorentz, x, y, p0=[width, pos, amp], bounds=bounds
            )

    if plot:
        plt.plot(x, y, ".k")
        plt.plot(x, func_invLorentz(x, *popt), "-r")
        plt.show()

    return popt, pcov


## function to fit 3D cavity spectroscopy traces
def fit_3DSpec(x, y, width, pos, amp, off=None, plot=False, bounds=None):
    if off is not None:
        if bounds is None:
            popt, pcov = opt.curve_fit(func_lorentz, x, y, p0=[width, pos, amp, off])
        else:
            popt, pcov = opt.curve_fit(
                func_lorentz, x, y, p0=[width, pos, amp, off], bounds=bounds
            )
    else:
        if bounds is None:
            popt, pcov = opt.curve_fit(func_lorentz, x, y, p0=[width, pos, amp])
        else:
            popt, pcov = opt.curve_fit(
                func_lorentz, x, y, p0=[width, pos, amp], bounds=bounds
            )

    if plot:
        plt.plot(x, y, ".k")
        plt.plot(x, func_lorentz(x, *popt), "-r")
        plt.show()

    return popt, pcov


## function to fit spectroscopy traces with Fano lineshape
def fit_ResSpec(x, y, width, pos, amp, fano, off=None, plot=False, bounds=None):
    if off is not None:
        if bounds is None:
            popt, pcov = opt.curve_fit(func_Fano, x, y, p0=[width, pos, amp, fano, off])
        else:
            popt, pcov = opt.curve_fit(
                func_Fano, x, y, p0=[width, pos, amp, fano, off], bounds=bounds
            )
    else:
        if bounds is None:
            popt, pcov = opt.curve_fit(func_Fano, x, y, p0=[width, pos, amp, fano])
        else:
            popt, pcov = opt.curve_fit(
                func_Fano, x, y, p0=[width, pos, amp, fano], bounds=bounds
            )

    if plot:
        plt.plot(x, y, ".k")
        plt.plot(x, func_Fano(x, *popt), "-r")
        plt.show()

    return popt, pcov

#########################################################################################
#PCA fitting
def normalize_1d_osc(osc, offset=None, norm=None):
    if offset is None:
        offset=np.mean(osc)
    if norm is None:
        norm = 1 / np.abs(osc.max() - osc.min())
    
    return 2 * (osc - offset) * norm, offset, norm

def compute_pca(i_data: NDArray, q_data: NDArray, plot=True, scaling_fac=0.1):
    assert i_data is not None and q_data is not None, "Provide both I and Q!"
    assert i_data.shape == q_data.shape, "I and Q must have same shape!"

    data = np.column_stack((i_data, q_data))
    data_center = np.array([np.mean(data[:, 0]), np.mean(data[:, 1])])
    n_comp = 2
    pca = PCA(n_components=n_comp)
    pca.fit(data)
    
    comps = pca.components_ / np.linalg.norm(pca.components_, axis=1) * np.abs(np.linalg.norm(data, axis=1).max()) * scaling_fac
    
    comp_dat = []    
    for i in [0, 1]:
        comp_dat.append([data.dot(comps[i]), data.dot(comps[1])])
        
    rdict = {'pca': pca, 
     'comp_1_I': comp_dat[0][0],
     'comp_1_Q': comp_dat[0][1],
     'comp_2_I': comp_dat[1][0],
     'comp_2_Q': comp_dat[1][1]}
      
    if plot:
        fig, axs = plt.subplots(n_comp + 1, 1, figsize=(10, int((n_comp+1) * 7)))
        axs[0].scatter(data[:, 0] - data_center[0], data[:, 1] - data_center[1], color='tab:blue', alpha=0.5, label='data')
        axs[0].plot([0, comps[0, 0]], [0, comps[0, 1]], linestyle='dashed', color='black', label='component 1')
        axs[0].plot([0, comps[1, 0]], [0, comps[1, 1]], linestyle='dotted', color='black', label='component 2')
        axs[0].set_aspect('equal', adjustable='datalim')
        axs[0].legend()
        axs[0].set_xlabel('I')
        axs[0].set_ylabel('Q')
        axs[0].set_title('Raw data and PCA components')
        
        axs[1].scatter(comp_dat[0][0], comp_dat[0][1])
        axs[1].set_title('Projected on component 1')
        
        axs[2].scatter(comp_dat[1][0], comp_dat[1][1])
        axs[2].set_title('Projected on component 2')
        
        rdict['fig_ax'] = (fig, axs)
    
    return rdict


def get_qrpm_dict_from_list_of_results(results):
    n = len(results)

    imax = np.zeros((n, 2))
    imin = np.zeros((n, 2))
    qmax = np.zeros((n, 2))
    qmin = np.zeros((n, 2))
    magmax = np.zeros((n, 2))
    magmin = np.zeros((n, 2))
    phamax = np.zeros((n, 2))
    phamin = np.zeros((n, 2))

    for i, res in enumerate(results):
        imax[i, 0] = res['with']['I_max']
        imin[i, 0] = res['with']['I_min']
        qmax[i, 0] = res['with']['Q_max']
        qmin[i, 0] = res['with']['Q_min']
        magmax[i, 0] = res['with']['mag_max']
        magmin[i, 0] = res['with']['mag_min']
        phamax[i, 0] = res['with']['pha_max']
        phamin[i, 0] = res['with']['pha_min']

        imax[i, 1] = res['wo']['I_max']
        imin[i, 1] = res['wo']['I_min']
        qmax[i, 1] = res['wo']['Q_max']
        qmin[i, 1] = res['wo']['Q_min']
        magmax[i, 1] = res['wo']['mag_max']
        magmin[i, 1] = res['wo']['mag_min']
        phamax[i, 1] = res['wo']['pha_max']
        phamin[i, 1] = res['wo']['pha_min']
    
    
    
    
    return {'I_max_with': imax[:, 0], 'I_min_with': imin[:, 0],
            'Q_max_with': qmax[:, 0], 'Q_min_with': qmin[:, 0],
            'mag_max_with': magmax[:, 0], 'mag_min_with': magmin[:, 0],
            'pha_max_with': phamax[:, 0], 'pha_min_with': phamin[:, 0],
            'I_max_wo': imax[:, 1], 'I_min_wo': imin[:, 1],
            'Q_max_wo': qmax[:, 1], 'Q_min_wo': qmin[:, 1],
            'mag_max_wo': magmax[:, 1], 'mag_min_wo': magmin[:, 1],
            'pha_max_wo': phamax[:, 1], 'pha_min_wo': phamin[:, 1]}

###############################################################################
#FFT and peack parameters detection
def FFT_analize(x, y, plot = False):
    
    #Make FFT
    dy = np.mean(y)
    y = y - dy

    N = len(x) #samples number
    T = x[1]-x[0] #sample spacing

    fy = fft.fft(y)
    fx = fft.fftfreq(N, T)[:N//2]

    if plot:
        plt.plot(fx, 2.0/N * np.abs(fy[0:N//2]), '.k')
        plt.yscale('log')
        plt.ylabel('Signal')
        plt.xlabel('Frequency')
    return fx, fy

def find_pick_param(x, y, sign = 1):
    if sign>0:
        opt_x = np.argmax(y)
    else:
        opt_x = np.argmin(y)
    x0 = x[opt_x]
    
    y_abs = abs(y)
    y0 = y_abs[opt_x]
    off = y_abs[-1]
    y2 = (y0-off)/2
    
    diff = abs(y_abs-y2)
    p_wx=np.argmin(diff)
    
    wx = abs(x0-x[p_wx])
    
    return x0, opt_x, wx, y0, off

def fit_FFT_spec(fx, fy, plot = False):
    N = len(fy)
    y = 2.0/N * np.abs(fy[0:N//2])
    x0, opt_x, wx, y0, off = find_pick_param(fx, y, sign = 1)
    
    popt, pcov = fit_Spec(fx, y, wx, x0, -y0*wx, off=off, plot=False, bounds=None)
    
    if plot:
        plt.plot(fx, y, 'o-')
        plt.plot(fx, func_invLorentz(fx, *popt))
        plt.xlabel('Freq., Hz')
        plt.ylabel('Abs, a.u.')
        plt.show()
        
    return popt, pcov

###################################################################################
#Data preparation functions

def find_rotation(data, plot = False):
    x = np.real(data)
    y = np.imag(data)
    
    popt, pcov = fit_linear(x, y, plot=plot)
    
    angle = np.arctan(popt[0])
    return angle

def rotate_and_norm(data, norm = False):
    angle = find_rotation(data, plot = False)
    
    data_rot = data*np.exp(-1j*angle)
    
    if norm:
        x = np.real(data_rot)
        min_el = np.min(x)
        max_el = np.max(x)
        dist = max_el-min_el
        result = (x-min_el)/dist
    else:
        result = data_rot
        
    return result
         
def reshape_to_1D(x):
    x_sh = x.shape
    if len(x_sh) != 1:
        x = np.reshape(x, (np.max(x_sh),))
    return x

def reshape_to_2D(x):
    x_sh = x.shape
    if len(x_sh) == 1:
        x = np.reshape(x, (1, x_sh[0]))
    return x

def average_by_key(data, markers):
    """Average all items in dictionary 'data', which has elements 'marker'
    in thier key
    data: dictionary
    marker: list of strings
    
    return: dictionary
    
    Example:
    'data' has kyes 'C1', 'C2', 'A1'. markers = ['C'].
    In this case, function will return dictionary with one key 'C' with result 
    (data['C1']+data['C2'])/2
    """
    data_av = {}
    for marker in markers:
        i = 0
        summ = 0
        for k in data.keys():
            if marker in k:
                summ = summ + data[k]
                i = i+1
        data_av[marker] = summ/i
    return data_av   

def average_by_N(arr1D, N):
    """Average every N sequential items in one-dimential array
    arr1D: 1D np.array, shape: (L,)
    N: int
    
    return: 1D np.array, shape: (L//N,)
    """
    if len(arr1D.shape) != 1:
        print('Input array is not 1D!')
        return None
    L = len(arr1D)
    result = np.zeros((L//N,))
    for i in range(L//N):
        start = N*i
        stop = N*i+N
        result[i] = np.nanmean(arr1D[start:stop])
    return result

def stretch_by_N(arr1D, N):
    """Reapeat N times each element in 1D array
    np.array, shape: (L,)
    N: int
    
    return: 1D np.array, shape: (L*N,)
    """
    if len(arr1D.shape) != 1:
        print('Input array is not 1D!')
        return None
    L = len(arr1D)
    result = np.zeros((N*L,))
    for i in range(L):
        for k in range(N):
            result[i*N+k] = arr1D[i]
    return result

def transform_complex_to_real(data, data_type = 'real'):
    data_sh = data.shape
    
    if len(data_sh) == 1:
        data = np.reshape(data, (1, data_sh[0]))
    
    #transform complex data to real
    if data_type == 'amp' or data_type == 'amplitude':
        data_trans = abs(data)
    elif data_type == 'phase':
        data_trans = np.unwrap(np.angle(data))
    elif data_type == 'real':  
        data_trans = np.real(data)
    elif data_type == 'imag':  
        data_trans = np.imag(data)
    elif data_type == 'rot' or data_type == 'rotation': 
        data_trans = np.zeros_like(data.real)
        for i in range(data.shape[0]):
            data_trans[i,:] = np.real(rotate_and_norm(data[i,:], norm = False))
    else:
        print('Unsupported data type! Type changed to real!')
        data = np.real(t1_data)
        
    return data_trans

#####################################################################################
#Fitting of the data for particular experiments


#T1 experiment
def auto_T1_fit(t1_delay, t1_data, data_type = 'real', plot = False):
    
    t1_delay = reshape_to_1D(t1_delay)
    
    #transform complex data to real
    data = transform_complex_to_real(t1_data, data_type = data_type)

    #prepare initial values
    popt = np.array([2e6, np.mean(data[0,:]), abs(np.max(data[0,:])-np.min(data[0,:]))])

    if np.argmax(data[0,:])>np.argmin(data[0,:]):
        sign = -1
    else:
        sign = 1
    
    popt_t1_list = []
    pcov_t1_list = []
    for i in range(data.shape[0]):
        try:
            popt, pcov = fit_T1(x = t1_delay, y = data[i,:], rate = popt[0], off = popt[1], amp = sign*popt[2], plot=plot)
        except:
            print('T1 Fit didnt converged!')
            popt = np.full((3,), np.nan)
            pcov = np.full((3,3), np.nan)
        popt_t1_list.append(popt)
        pcov_t1_list.append(pcov)

    popt_t1_arr = np.array(popt_t1_list)
    pcov_t1_arr = np.array(pcov_t1_list)
    return popt_t1_arr, pcov_t1_arr

#Ramsey experiment
def auto_ramsey_fit(ramsey_delay, ramsey_data, data_type = 'real', plot = False):
     #transform complex data to real
    data = transform_complex_to_real(ramsey_data, data_type = data_type)
    
    ramsey_delay = reshape_to_1D(ramsey_delay)
    N = len(ramsey_delay)
    
    popt_ramsey_list = []
    pcov_ramsey_list = []
    
    for i in range(data.shape[0]):
        #prepare initial values
        fx, fy = FFT_analize(ramsey_delay, data[i,:])
        y = 2.0/N * np.abs(fy[0:N//2])
        x0, opt_f, wx, y0, off = find_pick_param(fx, y, sign = 1)
        popt = np.array([x0*(2*np.pi), np.angle(fy[opt_f]), wx*(2*np.pi), (np.max(data[i,:])-np.min(data[i,:]))/2, np.mean(data[i,:])])

        #fit data
        try:
            popt, pcov = fit_Ramsey(
                ramsey_delay,
                data[i,:],
                popt[0], #frequency, radians!
                popt[1], #phase
                popt[2], #decay rate
                amp=popt[3], #amplitude
                off=popt[4], #offset
                plot=plot,
                bounds=[
                    [0.001e6, -1.5*np.pi, 1e3, 0.0001, -4],
                    [150e6, 1.5*np.pi, 1e8, 2, 4],
                ],
            )
        except:
            print('T2 Fit didnt converged!')
            popt = np.full((5,), np.nan)
            pcov = np.full((5,5), np.nan)
        popt_ramsey_list.append(popt)
        pcov_ramsey_list.append(pcov)

    popt_ramsey_arr = np.array(popt_ramsey_list)
    pcov_ramsey_arr = np.array(pcov_ramsey_list)
    return popt_ramsey_arr, pcov_ramsey_arr

def auto_ramsey_fit_freq(ramsey_delay, ramsey_data, data_type = 'real', plot = False):
    #transform complex data to real
    data = transform_complex_to_real(ramsey_data, data_type = data_type)

    ramsey_delay = reshape_to_1D(ramsey_delay)

    popt_ramsey_list = []
    pcov_ramsey_list = []
    
    for i in range(data.shape[0]):
        #prepare initial values
        fx, fy = FFT_analize(ramsey_delay, data[i,:])
        #fit data
        try:
            popt, pcov = fit_FFT_spec(fx, fy, plot = plot)
        except:
            print('T2 Fit didnt converged!')
            popt = np.full((4,), np.nan)
            pcov = np.full((4,4), np.nan)
        popt_ramsey_list.append(popt)
        pcov_ramsey_list.append(pcov)

    popt_ramsey_arr = np.array(popt_ramsey_list)
    pcov_ramsey_arr = np.array(pcov_ramsey_list)
    # popt = [width, position, amplitude, offset]!!!!
    return popt_ramsey_arr, pcov_ramsey_arr

def auto_echo_fit(echo_delay, echo_data, data_type = 'phase', plot = False):
    popt_echo_arr, pcov_echo_arr = auto_T1_fit(echo_delay*2, echo_data, data_type = data_type, plot = plot)
    return popt_echo_arr, pcov_echo_arr

######################################################################################
#Service functions
def check_reload():
    print('Thats example notebook helper')
    
################################################################################
#Error processing functions
def abs_err(pcov):
    sh = pcov.shape
    if len(sh)==3:
        err = np.zeros((sh[0], sh[1]))
        for i in range(sh[0]):
            err[i,:] = np.sqrt(np.diag(pcov[i,:,:]))
    else:
        err = np.sqrt(np.diag(pcov))
    return err

def rel_err(popt, pcov):
    err = abs_err(pcov)
    rel_err = abs(err/popt)
    return rel_err