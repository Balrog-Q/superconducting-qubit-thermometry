"""Single-shot (IQ blob) analysis helpers.

Used by the "Single Shot 0 and 1 Measurements" part of the Population &
Temperature Measurements notebook, and by any SINIS heating sweep that
optionally collects SSRO shots.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from laboneq.simple import dsl


def gauss(x, mu, sigma, A):
    """Single Gaussian: `A * exp(-((x - mu) ** 2) / 2 / sigma ** 2)`."""
    return A * np.exp(-((x - mu) ** 2) / 2 / sigma**2)


def bimodal(x, mu1, sigma1, A1, mu2, sigma2, A2):
    """Sum of two Gaussians, e.g. to fit a residual-population double peak."""
    return gauss(x, mu1, sigma1, A1) + gauss(x, mu2, sigma2, A2)


def collect_shots_from_result(result, qubit_uid: str, states: str) -> dict:
    """Single shots per prepared state from an `iq_blobs` workflow result."""
    return {
        s: result[dsl.handles.calibration_trace_handle(qubit_uid, s)].data for s in states
    }


def analyze_single_shots(shots_per_state, state_0="g", state_1="e", plot=False, n_bins=50):
    """Rotate two states' shots onto the state-discrimination axis and get its statistics.

    After the rotation, `state_0` sits on the negative and `state_1` on the
    positive real axis, so `shots_0_proj > 0` counts the misassigned
    `state_0` shots.
    """
    data_0 = np.asarray(shots_per_state[state_0])
    data_1 = np.asarray(shots_per_state[state_1])

    mean_0 = np.mean(data_0)
    mean_1 = np.mean(data_1)

    mid_point = 0.5 * (mean_0 + mean_1)

    data_0_corr = data_0 - mid_point
    data_1_corr = data_1 - mid_point

    distance = np.abs(mean_0 - mean_1) / 2
    phi = np.angle(mean_0 - mid_point)

    data_0_rot = data_0_corr * np.exp(1j * (np.pi - phi))
    data_1_rot = data_1_corr * np.exp(1j * (np.pi - phi))

    std_x_0 = np.sqrt(np.var(data_0_rot.real, ddof=1))
    std_y_0 = np.sqrt(np.var(data_0_rot.imag, ddof=1))
    std_x_1 = np.sqrt(np.var(data_1_rot.real, ddof=1))
    std_y_1 = np.sqrt(np.var(data_1_rot.imag, ddof=1))

    results = {
        "distance": distance,
        "mean_0": np.mean(data_0_rot),
        "mean_1": np.mean(data_1_rot),
        "std_x_0": std_x_0,
        "std_y_0": std_y_0,
        "std_x_1": std_x_1,
        "std_y_1": std_y_1,
        "rel_std_0": std_x_0 / distance,
        "rel_std_1": std_x_1 / distance,
        "shots_0_rot": data_0_rot,
        "shots_1_rot": data_1_rot,
        "shots_0_proj": data_0_rot.real,
        "shots_1_proj": data_1_rot.real,
        "n_misassigned_0": int(np.sum(data_0_rot.real > 0)),
        "n_assigned_0": int(np.sum(data_0_rot.real <= 0)),
    }

    if plot:
        fig, axs = plt.subplots(1, 2, sharey=True, tight_layout=True)
        fig.suptitle(f"Rotated single shots - {state_0} vs {state_1}")

        axs[0].set_title("Real")
        axs[0].hist(data_0_rot.real, bins=n_bins, alpha=0.5, label=state_0)
        axs[0].hist(data_1_rot.real, bins=n_bins, alpha=0.5, label=state_1)
        axs[0].set_yscale("log")
        axs[0].legend()

        axs[1].set_title("Imag")
        axs[1].hist(data_0_rot.imag, bins=n_bins, alpha=0.5, label=state_0)
        axs[1].hist(data_1_rot.imag, bins=n_bins, alpha=0.5, label=state_1)
        axs[1].set_yscale("log")
        axs[1].legend()

        results["figure"] = fig

    return results


def summarize_single_shot_metrics(res_ss, assignment_fidelity=None):
    """Compact printout of the figures of merit of one single-shot measurement."""
    print("State distance:          ", round(float(res_ss["distance"]), 6))
    print("Relative STD state 0:    ", round(float(res_ss["rel_std_0"]), 4))
    print("Relative STD state 1:    ", round(float(res_ss["rel_std_1"]), 4))
    print(
        "Misassigned state-0 shots:",
        res_ss["n_misassigned_0"],
        "/",
        res_ss["n_misassigned_0"] + res_ss["n_assigned_0"],
    )
    if assignment_fidelity is not None:
        print("Assignment fidelity:     ", f"{assignment_fidelity * 100:0.2f} %")
