"""Shared curve-fitting helpers.

`func_osc`/`fit_rabi_osc`/`normalize_1d_osc` are used by the Rabi Population
Measurement analysis; the rest (`func_exp`, `func_lin`, `fit_linear`,
`fit_T1`, `find_rotation`, `rotate_and_norm`, `reshape_to_1D`,
`transform_complex_to_real`, `auto_T1_fit`) are used by Fast Flux Drive
(decay-vs-flux fitting) and are generic enough to reuse anywhere a raw IQ
decay/oscillation trace needs fitting.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit


def func_osc(x, freq, phase, amp=1, off=0):
    """Cosine oscillation model: `amp * cos(freq * x + phase) + off`."""
    return amp * np.cos(freq * x + phase) + off


def fit_rabi_osc(x, y, freq, phase, amp=None, off=None, plot=False, bounds=None):
    """Fit `func_osc` to `(x, y)`, seeded with `freq`/`phase`(/`amp`/`off`)."""
    p0 = [freq, phase]
    if amp is not None:
        p0.append(amp)
        if off is not None:
            p0.append(off)

    kwargs = {} if bounds is None else {"bounds": bounds}
    popt, pcov = curve_fit(func_osc, x, y, p0=p0, **kwargs)

    if plot:
        plt.plot(x, y, ".k")
        plt.plot(x, func_osc(x, *popt), "-r")
        plt.xlabel("Amplitude, a.u.")
        plt.ylabel("Signal, a.u.")
        plt.show()

    return popt, pcov


def normalize_1d_osc(osc, offset=None, norm=None):
    """Center and scale a 1D oscillation trace to roughly [-1, 1]."""
    if offset is None:
        offset = np.mean(osc)
    if norm is None:
        norm = 1 / np.abs(osc.max() - osc.min())

    return 2 * (osc - offset) * norm, offset, norm


def func_exp(x, rate, off, amp=1):
    """Exponential decay model: `amp * exp(-rate * x) + off`."""
    return amp * np.exp(-rate * x) + off


def func_lin(x, a, b):
    """Linear model: `a * x + b`."""
    return a * x + b


def fit_linear(x, y, plot=False):
    """Fit `func_lin` to `(x, y)`."""
    popt, pcov = curve_fit(func_lin, x, y)
    if plot:
        plt.plot(x, y, ".k")
        plt.plot(x, func_lin(x, *popt), "-r")
        plt.show()
    return popt, pcov


def fit_T1(x, y, rate, off, amp=None, plot=False, bounds=None):
    """Fit `func_exp` (an exponential decay) to `(x, y)`."""
    p0 = [rate, off] if amp is None else [rate, off, amp]
    kwargs = {} if bounds is None else {"bounds": bounds}
    popt, pcov = curve_fit(func_exp, x, y, p0=p0, **kwargs)

    if plot:
        plt.plot(x, y, ".k")
        plt.plot(x, func_exp(x, *popt), "-r")
        plt.ylabel("Signal, a.u.")
        plt.xlabel("Delay, s")

    return popt, pcov


def find_rotation(data, plot=False):
    """Angle (rad) that best aligns complex `data` with the real axis."""
    popt, _pcov = fit_linear(np.real(data), np.imag(data), plot=plot)
    return np.arctan(popt[0])


def rotate_and_norm(data, norm=False):
    """Rotate complex `data` onto the real axis, optionally normalizing to [0, 1]."""
    angle = find_rotation(data, plot=False)
    data_rot = data * np.exp(-1j * angle)
    if norm:
        x = np.real(data_rot)
        return (x - np.min(x)) / (np.max(x) - np.min(x))
    return data_rot


def reshape_to_1D(x):
    """Flatten `x` to 1D if it is not already."""
    x_sh = x.shape
    if len(x_sh) != 1:
        x = np.reshape(x, (np.max(x_sh),))
    return x


def transform_complex_to_real(data, data_type="real"):
    """Project complex `data` (2D: [trace, point]) to a real-valued array.

    `data_type` is one of `"amp"`/`"amplitude"`, `"phase"`, `"real"`,
    `"imag"`, or `"rot"`/`"rotation"` (rotate each trace onto the real axis
    with `rotate_and_norm`).
    """
    data_sh = data.shape
    if len(data_sh) == 1:
        data = np.reshape(data, (1, data_sh[0]))

    if data_type in ("amp", "amplitude"):
        return np.abs(data)
    if data_type == "phase":
        return np.unwrap(np.angle(data))
    if data_type == "real":
        return np.real(data)
    if data_type == "imag":
        return np.imag(data)
    if data_type in ("rot", "rotation"):
        data_trans = np.zeros_like(data.real)
        for i in range(data.shape[0]):
            data_trans[i, :] = np.real(rotate_and_norm(data[i, :], norm=False))
        return data_trans

    print("Unsupported data type! Type changed to real!")
    return np.real(data)


def auto_T1_fit(t1_delay, t1_data, data_type="real", plot=False):
    """Fit an exponential decay to every row of `t1_data` vs. `t1_delay`.

    Returns `(popt_array, pcov_array)` with one fitted `(rate, off, amp)` per
    row of `t1_data`; rows whose fit does not converge are filled with NaN.
    """
    t1_delay = reshape_to_1D(t1_delay)
    data = transform_complex_to_real(t1_data, data_type=data_type)

    popt = np.array(
        [2e6, np.mean(data[0, :]), abs(np.max(data[0, :]) - np.min(data[0, :]))]
    )
    sign = -1 if np.argmax(data[0, :]) > np.argmin(data[0, :]) else 1

    popt_t1_list, pcov_t1_list = [], []
    for i in range(data.shape[0]):
        try:
            popt, pcov = fit_T1(
                t1_delay, data[i, :], rate=popt[0], off=popt[1], amp=sign * popt[2], plot=plot
            )
        except RuntimeError:
            print("T1 Fit did not converge!")
            popt = np.full((3,), np.nan)
            pcov = np.full((3, 3), np.nan)
        popt_t1_list.append(popt)
        pcov_t1_list.append(pcov)

    return np.array(popt_t1_list), np.array(pcov_t1_list)
