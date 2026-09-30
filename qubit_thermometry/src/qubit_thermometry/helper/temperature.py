"""Population -> pe/pg -> effective-temperature helpers.

Shared by the Population & Temperature Measurements, Fast Flux Drive and
SINIS Calibration workflows: all three run the six-sequence three-level
population protocol and then reduce it to `pe/pg` ratios (`A`/`B`/`C`
estimators) and effective temperatures with the functions in this module.
"""

from __future__ import annotations

import numpy as np
from laboneq.simple import dsl
from scipy.optimize import fsolve

# The six population labels of the three-level protocol.
pop_label_list = ["x0", "x1", "x2", "y0", "y1", "y2"]


def collect_population_from_result(result, qubit_uid, labels=pop_label_list):
    """The six population traces of a `population_experiment_workflow` result."""
    return {
        label: result[dsl.handles.result_handle(qubit_uid, suffix=label)].data
        for label in labels
    }


def qrpm_dict_from_results(results):
    """Flatten a list of RPM oscillation-fit result dicts into one dict of arrays.

    `results` is a list of `{"with": {...}, "wo": {...}}` dicts as built by
    `workflow.analysis.rabi_population`; each inner dict has keys `I_max`,
    `I_min`, `Q_max`, `Q_min`, `mag_max`, `mag_min`, `pha_max`, `pha_min`.
    """
    keys = ["I_max", "I_min", "Q_max", "Q_min", "mag_max", "mag_min", "pha_max", "pha_min"]
    out = {}
    for key in keys:
        for pre_pulse in ["with", "wo"]:
            out[f"{key}_{pre_pulse}"] = np.array(
                [np.mean(res[pre_pulse][key]) for res in results]
            )
    return out


def T_calc(C, f_q):
    """pe/pg (`C`) and `f_q` (GHz) -> temperature (K), two-level approximation."""
    h = 6.628e-2
    k = 1.381
    return -(h * f_q / k) / np.log(C)


def A_temp(T, A, f_q, anharm):
    """Residual of the `A` three-level estimator equation, for `fsolve`."""
    h = 6.628e-2
    k = 1.381
    f_g2 = 2 * f_q - anharm
    num = 1 - np.exp(-h * f_q / k / T)
    denum = 1 - np.exp(-h * f_g2 / k / T)
    return A - num / denum


def B_temp(T, B, f_q, anharm):
    """Residual of the `B` three-level estimator equation, for `fsolve`."""
    h = 6.628e-2
    k = 1.381
    f_g2 = 2 * f_q - anharm
    num = np.exp(-h * f_q / k / T) - np.exp(-h * f_g2 / k / T)
    denum = 1 - np.exp(-h * f_q / k / T)
    return B - num / denum


def C_temp(T, C, f_q, anharm):
    """Residual of the `C` three-level estimator equation, for `fsolve`."""
    h = 6.628e-2
    k = 1.381
    f_g2 = 2 * f_q - anharm
    num = np.exp(-h * f_q / k / T) - np.exp(-h * f_g2 / k / T)
    denum = 1 - np.exp(-h * f_g2 / k / T)
    return C - num / denum


def get_qubit_temperature_parameters(qubit):
    """`(f_q, anharm)` in GHz for `qubit`, derived from its resonance frequencies."""
    f_q = qubit.parameters.resonance_frequency_ge * 1e-9
    anharm = (
        qubit.parameters.resonance_frequency_ge - qubit.parameters.resonance_frequency_ef
    ) * 1e-9
    return f_q, anharm


def get_ABC(pop_proj):
    """The nine `A`/`B`/`C` estimators from projected (real- or imag-part) population data."""
    x0, x1, x2 = pop_proj["x0"], pop_proj["x1"], pop_proj["x2"]
    y0, y1, y2 = pop_proj["y0"], pop_proj["y1"], pop_proj["y2"]

    result = {}
    result["A1"] = (x0 - x1) / (y0 - y1)
    result["B1"] = (x2 - y2) / (x0 - x1)
    result["C1"] = result["A1"] * result["B1"]

    result["A2"] = (y0 - x2) / (x0 - y2)
    result["B2"] = (x1 - y1) / (y0 - x2)
    result["C2"] = result["A2"] * result["B2"]

    result["A3"] = (y1 - y2) / (x1 - x2)
    result["B3"] = (x0 - y0) / (y1 - y2)
    result["C3"] = result["A3"] * result["B3"]

    return result


def make_projection(pop_full_results, phase):
    """Rotate the six complex population traces by `phase` and split into I/Q."""
    res_I, res_Q = {}, {}
    for k in pop_full_results:
        rot = pop_full_results[k] * np.exp(1j * phase)
        res_I[k] = rot.real
        res_Q[k] = rot.imag
    return res_I, res_Q


def get_temperature(ABC, f_q, anharm=None, three_levels=False):
    """Effective temperature (mK) per `A`/`B`/`C` estimator.

    With `three_levels=False`, the simple low-temperature-limit closed form
    is used and `anharm` is ignored. With `three_levels=True`, each estimator
    is refined by solving the corresponding `A_temp`/`B_temp`/`C_temp`
    equation with `scipy.optimize.fsolve`, and `anharm` is required.
    """
    if three_levels and anharm is None:
        raise ValueError("`anharm` is required when `three_levels=True`.")

    def _pick(val, index):
        """Scalar for this element, whether `val` is a scalar or array-like."""
        arr = np.asarray(val)
        if arr.ndim == 0:
            return arr.item()
        return float(arr[index])

    result = {}
    for k in ABC:
        new_k = "T" + k
        if k[0] == "A":
            result[new_k] = T_calc(1 - ABC[k], f_q) * 1e3
            solve_fn = A_temp
        elif k[0] == "B":
            result[new_k] = T_calc(ABC[k] / (ABC[k] + 1), f_q) * 1e3
            solve_fn = B_temp
        elif k[0] == "C":
            result[new_k] = T_calc(ABC[k], f_q) * 1e3
            solve_fn = C_temp
        else:
            print("Wrong key in ABC dictionary!")
            continue

        if three_levels:
            for index, x in np.ndenumerate(ABC[k]):
                x0 = float(result[new_k][index]) * 1e-3
                f_q_i = _pick(f_q, index)
                anharm_i = _pick(anharm, index)
                root = fsolve(solve_fn, x0, args=(float(x), f_q_i, anharm_i))
                result[new_k][index] = float(root[0]) * 1e3

    return result


def get_stat(data):
    """`[mean, std, relative error]` per key of `data`."""
    stat = {}
    for k in data:
        arr = np.asarray(data[k], dtype=float)
        M = np.nanmean(arr)
        V = np.sqrt(np.var(arr, ddof=1))
        stat[k] = np.array([M, V, V / M], dtype=float)
        if stat[k].shape != (3,):
            raise RuntimeError(
                f"Unexpected stat shape for key {k!r}: {stat[k].shape}, "
                f"data shape was {arr.shape}"
            )
    return stat


def get_stat_nan(data):
    """Same as `get_stat`, but NaN-aware (`nanmean`/`nanvar`)."""
    stat = {}
    for k in data:
        M = np.nanmean(data[k])
        V = np.sqrt(np.nanvar(data[k], ddof=1))
        stat[k] = np.array([M, V, V / M])
    return stat


def make_all_temperatures(pop_full_results, f_q, anharm, phase=0, three_levels=True):
    """Project `pop_full_results` at `phase` and compute I/Q temperatures."""
    proj_I, proj_Q = make_projection(pop_full_results, phase)
    ABC_I = get_ABC(proj_I)
    ABC_Q = get_ABC(proj_Q)
    TABC_I = get_temperature(ABC_I, f_q, anharm, three_levels=three_levels)
    TABC_Q = get_temperature(ABC_Q, f_q, anharm, three_levels=three_levels)
    return TABC_I, TABC_Q


def get_diff(pop_proj):
    """The nine pairwise differences used by the 'parallel' ABC estimator."""
    x0, x1, x2 = pop_proj["x0"], pop_proj["x1"], pop_proj["x2"]
    y0, y1, y2 = pop_proj["y0"], pop_proj["y1"], pop_proj["y2"]

    diff_dict = {}
    # parallel to ge, index 1
    diff_dict["x0x1"] = x0 - x1  # order1, mid
    diff_dict["y0y1"] = y0 - y1  # order1, max
    diff_dict["x2y2"] = x2 - y2  # order0, min
    # parallel to gf, index 2
    diff_dict["y0x2"] = y0 - x2  # order1, mid
    diff_dict["x0y2"] = x0 - y2  # order1, max
    diff_dict["x1y1"] = x1 - y1  # order0, min
    # parallel to ef, index 3
    diff_dict["y1y2"] = y1 - y2  # order1, mid
    diff_dict["x1x2"] = x1 - x2  # order1, max
    diff_dict["x0y0"] = x0 - y0  # order0, min
    return diff_dict


def get_axes_and_rotate(D1, D2, D3):
    """Rotate the three difference vectors onto the real axis and form A/B/C."""
    angle1 = np.angle(D1)
    angle2 = np.angle(D2)
    angle = (angle1 + angle2) / 2
    D1_rot = D1 * np.exp(-1j * angle)
    D2_rot = D2 * np.exp(-1j * angle)
    D3_rot = D3 * np.exp(-1j * angle)

    A = D1_rot.real / D2_rot.real
    B = D3_rot.real / D1_rot.real
    C = D3_rot.real / D2_rot.real
    return A, B, C


def get_ABC_parallel(pop_full_results):
    """The nine `A`/`B`/`C` estimators using the 'parallel' (no manual phase) method."""
    diff_dict = get_diff(pop_full_results)

    result = {}
    result["A1"], result["B1"], result["C1"] = get_axes_and_rotate(
        diff_dict["x0x1"], diff_dict["y0y1"], diff_dict["x2y2"]
    )
    result["A2"], result["B2"], result["C2"] = get_axes_and_rotate(
        diff_dict["y0x2"], diff_dict["x0y2"], diff_dict["x1y1"]
    )
    result["A3"], result["B3"], result["C3"] = get_axes_and_rotate(
        diff_dict["y1y2"], diff_dict["x1x2"], diff_dict["x0y0"]
    )
    return result


def get_C_from_ABC(ABC_dict):
    """Every `A`/`B`/`C` estimator re-expressed as a `pe/pg`-like `C` estimator."""
    ccc_dict = {}
    for k in ABC_dict:
        kn = "C" + k
        if "A" in k:
            ccc_dict[kn] = 1 - ABC_dict[k]
        elif "B" in k:
            ccc_dict[kn] = ABC_dict[k] / (1 + ABC_dict[k])
        else:
            ccc_dict[kn] = ABC_dict[k]
    return ccc_dict


def make_rotation_temperature(data, phase_arr, f_q, anharm, three_levels=True):
    """Temperature statistics (`get_stat`) of every estimator, for each phase in `phase_arr`."""
    STAT_I, STAT_Q = {}, {}

    for i in range(len(phase_arr)):
        proj_I, proj_Q = make_projection(data, phase_arr[i])
        ABC_I = get_ABC(proj_I)
        ABC_Q = get_ABC(proj_Q)
        TABC_I = get_temperature(ABC_I, f_q, anharm, three_levels=three_levels)
        TABC_Q = get_temperature(ABC_Q, f_q, anharm, three_levels=three_levels)

        stat_TABC_I = get_stat(TABC_I)
        stat_TABC_Q = get_stat(TABC_Q)
        for k in stat_TABC_I:
            if i == 0:
                STAT_I[k] = [stat_TABC_I[k]]
                STAT_Q[k] = [stat_TABC_Q[k]]
            else:
                STAT_I[k].append(stat_TABC_I[k])
                STAT_Q[k].append(stat_TABC_Q[k])

    for k in STAT_I:
        STAT_I[k] = np.array(STAT_I[k])
        STAT_Q[k] = np.array(STAT_Q[k])

    return STAT_I, STAT_Q


def make_optimal_temperature(
    data, phase_arr, f_q, anharm, skip=(), info_type="rel_err", three_levels=True
):
    """Find the `(estimator, phase, I/Q axis)` combination with the lowest `info_type`."""
    STAT_I, STAT_Q = make_rotation_temperature(data, phase_arr, f_q, anharm, three_levels=three_levels)

    optimal_method = {"rel_err": 1000, "phase": 0, "ph_p": 0, "method": "0", "axes": "0"}
    it = {"mean": 0, "error": 1, "rel_err": 2}[info_type]

    for k in STAT_I:
        if k in skip:
            continue
        rel_Q = np.nanmin(STAT_Q[k][:, it])
        ph_p_Q = np.nanargmin(STAT_Q[k][:, it])
        rel_I = np.nanmin(STAT_I[k][:, it])
        ph_p_I = np.nanargmin(STAT_I[k][:, it])

        if (rel_I or ph_p_Q) < optimal_method["rel_err"]:
            optimal_method["method"] = k
            if abs(phase_arr[ph_p_Q]) < abs(phase_arr[ph_p_I]):
                optimal_method["rel_err"] = rel_Q
                optimal_method["phase"] = phase_arr[ph_p_Q]
                optimal_method["ph_p"] = ph_p_Q
                optimal_method["axes"] = "Q"
            else:
                optimal_method["rel_err"] = rel_I
                optimal_method["phase"] = phase_arr[ph_p_I]
                optimal_method["ph_p"] = ph_p_I
                optimal_method["axes"] = "I"
    return optimal_method


def find_optimal_temperature(pop_full_results, optimal_method, f_q, anharm, three_levels=True):
    """Temperature trace for the `optimal_method` found by `make_optimal_temperature`."""
    proj_I, proj_Q = make_projection(pop_full_results, optimal_method["phase"])

    if optimal_method["axes"] == "I":
        ABC = get_ABC(proj_I)
    elif optimal_method["axes"] == "Q":
        ABC = get_ABC(proj_Q)
    else:
        print("Wrong axe in optimal_parameters!")
        return None

    TABC = get_temperature(ABC, f_q, anharm, three_levels=three_levels)
    return TABC[optimal_method["method"]]
