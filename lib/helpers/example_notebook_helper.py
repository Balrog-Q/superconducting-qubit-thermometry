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

from laboneq.dsl import device
from laboneq.simulator.output_simulator import OutputSimulator
import re

from numpy.typing import NDArray

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


def plot_simulation(
    compiled_experiment,
    start_time=0.0,
    length=10e-6,
    xaxis_label="Time (s)",
    yaxis_label="Amplitude",
    plot_width=6,
    plot_height=2,
):
    simulation=OutputSimulator(compiled_experiment)

    mapped_signals = compiled_experiment.experiment.signal_mapping_status[
        "mapped_signals"
    ]

    xs = []
    y1s = []
    labels1 = []
    y2s = []
    labels2 = []
    for signal in mapped_signals:
        mapped_path = compiled_experiment.experiment.signals[
            signal
        ].mapped_logical_signal_path

        full_path = re.sub(r"/logical_signal_groups/", "", mapped_path)
        signal_group_name = re.sub(r"/[^/]*$", "", full_path)
        signal_line_name = re.sub(r".*/", "", full_path)

        physical_channel_path = (
            compiled_experiment.device_setup.logical_signal_groups[signal_group_name]
            .logical_signals[signal_line_name]
            .physical_channel
        )

        my_snippet=simulation.get_snippet(
            compiled_experiment.device_setup.logical_signal_groups[
                signal_group_name
            ]
            .logical_signals[signal_line_name]
            .physical_channel,
            start=start_time,
            output_length=length,
            get_trigger=True,
            get_frequency=True,
        )

        if "iq_channel" in str(
            physical_channel_path.type
        ).lower() and "input" not in str(physical_channel_path.name):
            
            try:
                if my_snippet.time is not None:
                    xs.append(
                        my_snippet.time
                    )

                    y1s.append(
                        my_snippet.wave.real
                    )
                    labels1.append(f"{signal} I")

                    y2s.append(
                        my_snippet.wave.imag
                    )
                    labels2.append(f"{signal} Q")
            except Exception:
                pass

        if (
            "iq_channel" not in str(physical_channel_path.type).lower()
            or "input" in physical_channel_path.name
        ):
            try:
                if my_snippet.time is not None:
                    time_length = len(
                        my_snippet.time
                    )

                    xs.append(
                        my_snippet.time
                    )

                    y1s.append(
                        my_snippet.wave.real
                    )
                    labels1.append(f"{signal}")

                    empty_array = np.empty((1, time_length))
                    empty_array.fill(np.nan)
                    y2s.append(empty_array[0])
                    labels2.append(None)

            except Exception:
                pass

    colors = plt.rcParams["axes.prop_cycle"]()

    fig, axes = plt.subplots(
        nrows=len(y1s),
        sharex=False,
        figsize=(plot_width, len(mapped_signals) * plot_height),
    )

    if len(mapped_signals) > 1:
        for axs, x, y1, y2, label1, label2 in zip(
            axes.flat, xs, y1s, y2s, labels1, labels2
        ):
            # Get the next color from the cycler
            c = next(colors)["color"]
            axs.plot(x, y1, label=label1, color=c)
            c = next(colors)["color"]
            axs.plot(x, y2, label=label2, color=c)
            axs.set_ylabel(yaxis_label)
            axs.set_xlabel(xaxis_label)
            axs.legend(loc="upper right")
            axs.ticklabel_format(axis="both", style="sci", scilimits=(0, 0))
            axs.grid(True)

    elif len(mapped_signals) == 1:
        for x, y1, y2, label1, label2 in zip(xs, y1s, y2s, labels1, labels2):
            # Get the next color from the cycler
            c = next(colors)["color"]
            axes.plot(x, y1, label=label1, color=c)
            c = next(colors)["color"]
            axes.plot(x, y2, label=label2, color=c)
            axes.set_ylabel(yaxis_label)
            axes.set_xlabel(xaxis_label)
            axes.legend(loc="upper right")
            axes.ticklabel_format(axis="both", style="sci", scilimits=(0, 0))
            axes.grid(True)

    fig.tight_layout()
    # fig.legend(loc="upper left")
    plt.show()


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


## Definitions for fitting experimental data - needed to extract qubit paramters
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

## function to fit linear dependances
def fit_linear(x, y, plot=False):

    popt, pcov = opt.curve_fit(func_lin, x, y)
    
    if plot:
        plt.plot(x, y, ".k")
        plt.plot(x, func_lin(x, *popt), "-r")
        plt.show()

    return popt, pcov

## function to fit Rabi oscillations
def fit_Rabi(x, y, freq, phase, amp=None, off=None, plot=False, bounds=None):
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
        plt.show()

    return popt, pcov


## function to fit Ramsey oscillations
def fit_Ramsey(x, y, freq, phase, rate, amp=None, off=None, plot=False, bounds=None):
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


## function to fit T1 decay
def fit_T1(x, y, rate, off, amp=None, plot=False, bounds=None):
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
        plt.show()

    return popt, pcov

## function to fit T1 decay for ef level
def fit_T1_ef(x, y, rate1, rate2, off, A = 0.1, B = 0.1, plot=False, bounds=None):
    p0 = [rate1, rate2, off, A, B]
    
    if bounds is None:
        popt, pcov = opt.curve_fit(func_two_exp, x, y, p0=p0)
    else:
        popt, pcov = opt.curve_fit(func_two_exp, x, y, p0=p0, bounds=bounds)

    if plot:
        plt.plot(x, y, ".k")
        plt.plot(x, func_two_exp(x, *popt), "-r")
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

# ## function to fit T1 decay
# def fit_T1(x, y, rate, off, amp=None, plot=False, bounds=None):
#     if bounds is None:
#         if amp is None:
#             popt, pcov = opt.curve_fit(func_exp, x, y, p0=[rate, off])
#         else:
#             popt, pcov = opt.curve_fit(func_exp, x, y, p0=[rate, off, amp])
#     else:
#         if amp is None:
#             popt, pcov = opt.curve_fit(func_exp, x, y, p0=[rate, off], bounds=bounds)
#         else:
#             popt, pcov = opt.curve_fit(
#                 func_exp, x, y, p0=[rate, off, amp], bounds=bounds
#             )

#     if plot:
#         plt.plot(x, y, ".k")
#         plt.plot(x, func_exp(x, *popt), "-r")
#         plt.show()

#     return popt, np.sqrt(np.diag(pcov))

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

def auto_T1_fit(t1_delay, t1_data, data_type = 'phase', plot = False):
    #transform complex data to real
    if data_type == 'amp':
        data = abs(t1_data)
    elif data_type == 'phase':
        data = np.unwrap(np.angle(t1_data))
    elif data_type == 'real':  
        data = np.real(t1_data)
    elif data_type == 'imag':  
        data = np.imag(t1_data)
    else:
        print('Unsupported data type! Type changed to phase!')
        data = np.unwrap(np.angle(t1_data))

    #check shape of the data
    data_sh = data.shape
    x_sh = t1_delay.shape

    if len(data_sh) == 1:
        data = np.reshape(data, (1, data_sh[0]))

    #prepare initial values
    popt = np.array([2e6, np.mean(data[0,:]), abs(np.max(data[0,:])-np.min(data[0,:]))])

    popt_t1_list = []
    pcov_t1_list = []
    for i in range(data.shape[0]):
        try:
            popt, pcov = fit_T1(x = t1_delay, y = data[i,:], rate = popt[0], off = popt[1], amp = -popt[2], plot=plot)
        except:
            print('T1 Fit didnt converged!')
        popt_t1_list.append(popt)
        pcov_t1_list.append(pcov)

    popt_t1_arr = np.array(popt_t1_list)
    pcov_t1_arr = np.array(pcov_t1_list)
    return popt_t1_arr, pcov_t1_arr


def auto_ramsey_fit(ramsey_delay, ramsey_data, data_type = 'phase', plot = False):
    #transform complex data to real
    if data_type == 'amp':
        data = abs(ramsey_data)
    elif data_type == 'phase':
        data = np.unwrap(np.angle(ramsey_data))
    elif data_type == 'real':  
        data = np.real(ramsey_data)
    elif data_type == 'imag':  
        data = np.imag(ramsey_data)
    else:
        print('Unsupported data type! Type changed to phase!')
        data = np.unwrap(np.angle(ramsey_data))

    #check shape of the data
    data_sh = data.shape
    x_sh = ramsey_delay.shape

    if len(data_sh) == 1:
        data = np.reshape(data, (1, data_sh[0]))

    # #prepare initial values
    # fx, fy = FFT_analize(ramsey_delay, data[0,:])
    # opt_f = np.argmax(abs(fy))
    # popt = np.array([fx[opt_f], 0, 2 / 6e-7, np.max(data[0,:])-np.min(data[0,:]), np.mean(data[0,:])])

    #popt = np.array([4e6, 0, 2 / 6e-7, 0.01, -0.75])

    popt_ramsey_list = []
    pcov_ramsey_list = []
    for i in range(data.shape[0]):
        #prepare initial values
        fx, fy = FFT_analize(ramsey_delay, data[i,:])
        opt_f = np.argmax(abs(fy))
        popt = np.array([fx[opt_f], 0, 2 / 6e-7, np.max(data[i,:])-np.min(data[i,:]), np.mean(data[i,:])])

        #fit data
        try:
            popt, pcov = fit_Ramsey(
                ramsey_delay,
                data[i,:],
                popt[0],
                popt[1],
                popt[2],
                amp=popt[3],
                off=popt[4],
                plot=plot,
                bounds=[
                    [0.001e6, -1.5*np.pi, 0.05 / 6e-7, 0.0001, -4],
                    [150e6, 1.5*np.pi, 30 / 6e-7, 2, 4],
                ],
            )
        except:
            print('T2 Fit didnt converged!')
        popt_ramsey_list.append(popt)
        pcov_ramsey_list.append(pcov)

    popt_ramsey_arr = np.array(popt_ramsey_list)
    pcov_ramsey_arr = np.array(pcov_ramsey_list)
    return popt_ramsey_arr, pcov_ramsey_arr

def auto_echo_fit(echo_delay, echo_data, data_type = 'phase', plot = False):
    popt_echo_arr, pcov_echo_arr = auto_T1_fit(echo_delay*2, echo_data, data_type = data_type, plot = plot)
    return popt_echo_arr, pcov_echo_arr

def check_reload():
    print('Thats example notebook helper')