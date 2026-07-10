"""Single tone spectroscopy (STS) resonator fitting.

This module provides self-contained replacements for the ``scresonators``
wrapper functions used in the measurement notebooks
(``S3_Q2_Cooldown_2.ipynb`` / ``slicing_code/2-spectroscopy.ipynb``)::

    from scresonators import fit_single_STS_wrapper, plot_single_STS_wrapper

    full_result, quick_result, sweep_manager = fit_single_STS_wrapper(
        freqs=spec_freq, y_data=spec_res
    )
    print(quick_result)
    fig, ax = plot_single_STS_wrapper(sweep_man=sweep_manager)

``fit_single_STS_wrapper`` fits a single resonator spectroscopy trace (complex
S21 vs. frequency) to the asymmetric Lorentzian / Diameter-Correction-Method
(DCM) model for a notch (hanger) type resonator and extracts the resonance
frequency ``f0`` and the internal and coupling quality factors ``qi``/``qc``.
It returns three objects mirroring the original wrapper:

* ``full_result``  - a dict with every fitted and derived parameter, the
  parameter covariance and the model curve used for plotting.
* ``quick_result`` - a compact dict ``{f0, f0_sigma, qc, qc_sigma, qi,
  qi_sigma}`` (the values the notebook prints and uses to update
  ``qubit_parameters['ro_freq']``).
* ``sweep_manager`` - a :class:`SweepManager` holding the raw data, metadata
  and the fit results. It is the object consumed by
  ``plot_single_STS_wrapper``.

The implementation only depends on numpy / scipy / matplotlib (all already in
``requirements.txt``) so the notebook no longer needs the external
``scresonators`` package to run.

Model (Khalil et al., J. Appl. Phys. 111, 054510 (2012))::

    S21(f) = a * exp(i*alpha) * exp(-2j*pi*(f - f_ref)*tau)
             * (1 - (Q/|Qc|) * exp(i*phi) / (1 + 2j*Q*(f - f0)/f0))

with the DCM relation ``1/Qi = 1/Q - cos(phi)/|Qc|``.
"""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

__all__ = [
    "SweepManager",
    "fit_single_STS_wrapper",
    "plot_single_STS_wrapper",
]

# Order of the fitted parameters of the complex DCM model.
_PARAM_NAMES = ("a", "alpha", "tau", "Q", "Qc", "phi", "f0")


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
def _dcm_notch(freqs, a, alpha, tau, Q, Qc, phi, f0, f_ref):
    """Complex S21 of a notch resonator including a simple environment.

    ``a``     amplitude scaling of the background
    ``alpha`` constant phase offset
    ``tau``   electrical (cable) delay
    ``Q``     loaded quality factor
    ``Qc``    magnitude of the coupling quality factor
    ``phi``   impedance-mismatch (asymmetry) angle
    ``f0``    resonance frequency
    ``f_ref`` reference frequency for the delay term (kept fixed)
    """
    x = (freqs - f0) / f0
    env = a * np.exp(1j * alpha) * np.exp(-2j * np.pi * (freqs - f_ref) * tau)
    resonator = 1.0 - (Q / Qc) * np.exp(1j * phi) / (1.0 + 2j * Q * x)
    return env * resonator


def _qi_from_dcm(Q, Qc, phi):
    """Internal quality factor from the DCM relation."""
    denom = 1.0 / Q - np.cos(phi) / Qc
    if denom <= 0:
        return np.inf
    return 1.0 / denom


# ---------------------------------------------------------------------------
# Initial guesses
# ---------------------------------------------------------------------------
def _initial_guess(freqs, s21):
    """Estimate starting parameters from the raw complex trace."""
    mag = np.abs(s21)
    n_edge = max(1, len(freqs) // 10)

    # Baseline amplitude from the off-resonant band edges.
    edge_mag = np.concatenate([mag[:n_edge], mag[-n_edge:]])
    a0 = float(np.mean(edge_mag)) or float(np.max(mag)) or 1.0

    # Resonance sits at the magnitude minimum (a dip for a notch resonator).
    idx_min = int(np.argmin(mag))
    f0 = float(freqs[idx_min])

    # Electrical delay from the slope of the unwrapped phase over the band.
    phase = np.unwrap(np.angle(s21))
    slope = np.polyfit(freqs, phase, 1)[0]
    tau0 = -slope / (2.0 * np.pi)

    # Constant phase offset after removing the delay guess.
    f_ref = float(freqs[0])
    de_delayed = s21 * np.exp(2j * np.pi * (freqs - f_ref) * tau0)
    alpha0 = float(np.angle(np.mean(de_delayed)))

    # Loaded Q from the -3 dB (half-depth) width of the dip.
    depth = a0 - mag[idx_min]
    half = a0 - depth / 2.0
    below = np.where(mag <= half)[0]
    if below.size >= 2:
        fwhm = abs(freqs[below[-1]] - freqs[below[0]])
    else:
        fwhm = abs(freqs[-1] - freqs[0]) / 10.0
    fwhm = fwhm or (abs(freqs[-1] - freqs[0]) / 10.0)
    Q0 = f0 / fwhm

    # Coupling Q from the dip depth: |S21|_min / a = |1 - Q/Qc|.
    ratio = np.clip(mag[idx_min] / a0, 0.0, 0.999)
    Qc0 = Q0 / max(1.0 - ratio, 1e-3)

    return {
        "a": a0,
        "alpha": alpha0,
        "tau": tau0,
        "Q": Q0,
        "Qc": Qc0,
        "phi": 0.0,
        "f0": f0,
    }, f_ref


# ---------------------------------------------------------------------------
# Core fit
# ---------------------------------------------------------------------------
def _fit_dcm(freqs, s21):
    """Fit the complex DCM notch model. Returns (popt, pcov, f_ref)."""
    guess, f_ref = _initial_guess(freqs, s21)
    p0 = [guess[name] for name in _PARAM_NAMES]

    span = abs(freqs[-1] - freqs[0]) or 1.0
    lower = [0.0, -np.inf, -np.inf, 1.0, 1.0, -np.pi / 2, freqs.min() - span]
    upper = [np.inf, np.inf, np.inf, np.inf, np.inf, np.pi / 2, freqs.max() + span]
    # Keep the initial guess strictly inside the bounds.
    p0 = [min(max(v, lo + 1e-12), hi - 1e-12) for v, lo, hi in zip(p0, lower, upper)]

    target = np.concatenate([s21.real, s21.imag])

    def stacked(f, a, alpha, tau, Q, Qc, phi, f0):
        model = _dcm_notch(f, a, alpha, tau, Q, Qc, phi, f0, f_ref)
        return np.concatenate([model.real, model.imag])

    popt, pcov = curve_fit(
        stacked, freqs, target, p0=p0, bounds=(lower, upper), maxfev=100000
    )
    return popt, pcov, f_ref


def _reduced_chi_squared(freqs, s21, popt, f_ref):
    model = _dcm_notch(freqs, *popt, f_ref=f_ref)
    residual = np.concatenate([(s21 - model).real, (s21 - model).imag])
    dof = max(len(residual) - len(popt), 1)
    return float(np.sum(residual ** 2) / dof)


def _qi_uncertainty(popt, pcov):
    """Propagate the covariance of (Q, Qc, phi) onto Qi."""
    _, _, _, Q, Qc, phi, _ = popt
    Qi = _qi_from_dcm(Q, Qc, phi)
    if not np.isfinite(Qi):
        return np.inf
    # Partial derivatives of Qi w.r.t. Q, Qc, phi (indices 3, 4, 5).
    dQi_dQ = Qi ** 2 / Q ** 2
    dQi_dQc = -(Qi ** 2) * np.cos(phi) / Qc ** 2
    dQi_dphi = -(Qi ** 2) * np.sin(phi) / Qc
    jac = np.array([dQi_dQ, dQi_dQc, dQi_dphi])
    sub_cov = pcov[np.ix_([3, 4, 5], [3, 4, 5])]
    var = float(jac @ sub_cov @ jac)
    return float(np.sqrt(var)) if var > 0 else np.inf


# ---------------------------------------------------------------------------
# Sweep manager
# ---------------------------------------------------------------------------
class SweepManager:
    """Container holding a resonator spectroscopy trace and its fit.

    This is a light-weight stand-in for the ``scresonators`` sweep manager.
    It stores the raw data plus optional sweep metadata (temperature,
    attenuation/power) and, once :meth:`fit` has run, the fit results used by
    :func:`plot_single_STS_wrapper`.
    """

    def __init__(
        self,
        freqs: Sequence[float],
        s21: Sequence[complex],
        temperatures: Optional[Sequence[float]] = None,
        powers: Optional[Sequence[float]] = None,
        attenuation: Optional[float] = None,
        verbose: bool = True,
    ):
        freqs = np.asarray(freqs, dtype=float).ravel()
        s21 = np.asarray(s21).ravel()
        if freqs.shape != s21.shape:
            raise ValueError(
                f"freqs and y_data must have the same length, got "
                f"{freqs.shape} and {s21.shape}."
            )
        if not np.iscomplexobj(s21):
            # Allow magnitude-only input; phase is then unavailable.
            s21 = s21.astype(complex)

        self.freqs = freqs
        self.s21 = s21
        self.temperatures = np.atleast_1d(
            np.asarray([0.0] if temperatures is None else temperatures, dtype=float)
        )
        self.powers = np.atleast_1d(
            np.asarray([0.0] if powers is None else powers, dtype=float)
        )
        self.attenuation = attenuation
        self.verbose = verbose

        self.full_result: Optional[dict] = None
        self.quick_result: Optional[dict] = None

    # -- logging ---------------------------------------------------------
    def _log(self, message: str) -> None:
        if self.verbose:
            print(message)

    # -- fitting ---------------------------------------------------------
    def fit(self) -> Tuple[dict, dict]:
        """Fit the stored trace and populate ``full_result``/``quick_result``."""
        if self.attenuation is None:
            self._log(
                "WARNING: Neither manual attenuation nor attenuation field "
                "names in matlab file were supplied. Assuming 0dB attenuation."
            )
            self.attenuation = 0.0

        self._log("INFO: *STS Fitter* loaded data from 1 measurements.")
        self._log(f"INFO: temperatures (mK): {self.temperatures.astype(int).tolist()}")
        self._log(f"INFO:  (): {self.powers.astype(int).tolist()}")
        self._log("INFO: *STS Fitter* started fitting resonance curves.")

        popt, pcov, f_ref = _fit_dcm(self.freqs, self.s21)
        perr = np.sqrt(np.abs(np.diag(pcov)))

        params = dict(zip(_PARAM_NAMES, (float(v) for v in popt)))
        errors = {f"{name}_sigma": float(e) for name, e in zip(_PARAM_NAMES, perr)}

        Qi = _qi_from_dcm(params["Q"], params["Qc"], params["phi"])
        Qi_sigma = _qi_uncertainty(popt, pcov)

        fine_freqs = np.linspace(self.freqs.min(), self.freqs.max(), 1001)
        fit_s21 = _dcm_notch(fine_freqs, *popt, f_ref=f_ref)

        self.full_result = {
            "params": params,
            "errors": errors,
            "Qi": float(Qi),
            "Qi_sigma": float(Qi_sigma),
            "covariance": pcov,
            "f_ref": f_ref,
            "reduced_chi_squared": _reduced_chi_squared(
                self.freqs, self.s21, popt, f_ref
            ),
            "fit_freqs": fine_freqs,
            "fit_s21": fit_s21,
        }

        self.quick_result = {
            "f0": np.float64(params["f0"]),
            "f0_sigma": np.float64(errors["f0_sigma"]),
            "qc": np.float64(params["Qc"]),
            "qc_sigma": np.float64(errors["Qc_sigma"]),
            "qi": np.float64(Qi),
            "qi_sigma": np.float64(Qi_sigma),
        }

        self._log("INFO: *STS Fitter* is done!")
        return self.full_result, self.quick_result

    # -- plotting --------------------------------------------------------
    def plot(self, ax: Optional[plt.Axes] = None):
        """Plot the magnitude data with the fitted resonance overlaid."""
        if self.full_result is None:
            raise RuntimeError("Call fit() before plotting.")

        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        ghz = 1e-9
        f0 = self.full_result["params"]["f0"]

        ax.plot(
            self.freqs * ghz,
            np.abs(self.s21),
            ".",
            color="#006699",
            label="data",
        )
        ax.plot(
            self.full_result["fit_freqs"] * ghz,
            np.abs(self.full_result["fit_s21"]),
            "-",
            color="#FF0000",
            label="DCM fit",
        )
        ax.axvline(f0 * ghz, color="0.5", ls="--", lw=1.0)

        qi = self.full_result["Qi"]
        qc = self.full_result["params"]["Qc"]
        ax.set_title(
            f"$f_0$ = {f0 * 1e-9:.6f} GHz, $Q_i$ = {qi:.0f}, $Q_c$ = {qc:.0f}"
        )
        ax.set_xlabel("Frequency (GHz)")
        ax.set_ylabel("|S21| (a.u.)")
        ax.legend()
        fig.tight_layout()
        return fig, ax


# ---------------------------------------------------------------------------
# Wrapper functions (public API matching the notebooks)
# ---------------------------------------------------------------------------
def fit_single_STS_wrapper(
    freqs: Sequence[float],
    y_data: Sequence[complex],
    temperatures: Optional[Sequence[float]] = None,
    powers: Optional[Sequence[float]] = None,
    attenuation: Optional[float] = None,
    verbose: bool = True,
) -> Tuple[dict, dict, SweepManager]:
    """Fit a single resonator spectroscopy trace.

    Parameters
    ----------
    freqs:
        Frequency axis in Hz.
    y_data:
        Complex S21 (or magnitude) measured at each frequency.
    temperatures, powers:
        Optional sweep metadata, only used for logging/bookkeeping.
    attenuation:
        Line attenuation in dB. If ``None`` a 0 dB attenuation is assumed
        (a warning is emitted, mirroring the original STS fitter).
    verbose:
        Print the informational messages of the STS fitter.

    Returns
    -------
    full_result : dict
        All fitted and derived parameters plus the model curve.
    quick_result : dict
        ``{f0, f0_sigma, qc, qc_sigma, qi, qi_sigma}``.
    sweep_manager : SweepManager
        The fitted sweep manager (input to :func:`plot_single_STS_wrapper`).
    """
    sweep_manager = SweepManager(
        freqs=freqs,
        s21=y_data,
        temperatures=temperatures,
        powers=powers,
        attenuation=attenuation,
        verbose=verbose,
    )
    full_result, quick_result = sweep_manager.fit()
    return full_result, quick_result, sweep_manager


def plot_single_STS_wrapper(
    sweep_man: SweepManager,
    ax: Optional[plt.Axes] = None,
) -> Tuple[plt.Figure, plt.Axes]:
    """Plot the fit stored in ``sweep_man``.

    Returns the matplotlib ``(figure, axes)`` so callers can further annotate
    or save the plot, matching the notebook usage
    ``fig, ax = plot_single_STS_wrapper(sweep_man=sweep_manager)``.
    """
    return sweep_man.plot(ax=ax)


if __name__ == "__main__":
    # Minimal self-test on synthetic data (no hardware required).
    rng = np.random.default_rng(0)
    true = dict(a=0.8, alpha=0.4, tau=1.5e-8, Q=19600.0, Qc=26500.0, phi=0.05,
                f0=6.336e9)
    f = np.linspace(true["f0"] - 5e6, true["f0"] + 5e6, 201)
    clean = _dcm_notch(f, true["a"], true["alpha"], true["tau"], true["Q"],
                       true["Qc"], true["phi"], true["f0"], f_ref=f[0])
    noisy = clean + (rng.normal(0, 0.01, f.size) + 1j * rng.normal(0, 0.01, f.size))

    full, quick, sm = fit_single_STS_wrapper(freqs=f, y_data=noisy)
    print(quick)
    print("Qi(true)=%.0f  Qc(true)=%.0f  f0(true)=%.6f GHz"
          % (_qi_from_dcm(true["Q"], true["Qc"], true["phi"]), true["Qc"],
             true["f0"] * 1e-9))
    plot_single_STS_wrapper(sweep_man=sm)
    plt.show()
