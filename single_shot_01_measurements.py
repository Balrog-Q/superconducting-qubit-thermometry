"""Single Shot 0 and 1 Measurements — cell-by-cell code for ES-008-BC_2-1_8853_Q3_CD3.

Port of the "Single Shot 0 and 1 measurements" section of `S3_Q2_Cooldown_2.json`
(old, hand-rolled LabOne Q DSL, cells 275-327) to the LabOneQ *workflow*
architecture and the layout used by `ES-008-BC_2-1_8853_Q3_CD3.json`
(`## Section` -> `#### Experiment Parameters` / `#### Run Workflow` /
`#### Analysis Plots` / `#### Update Parameters`).

Cells are delimited with jupytext markers:
    `# %% [markdown]`  -> markdown cell
    `# %%`             -> code cell
Copy each block into its own notebook cell, replacing the empty cell 103 under
the existing `# Single Shot 0 and 1 Measurements` heading (cell 102). The first
markdown block below is identical to cell 102, so you may skip it.

-------------------------------------------------------------------------------
OLD -> NEW PARAMETER / API NAME MAPPING
-------------------------------------------------------------------------------
Qubit parameters (old `qubit_parameters[...]` / `lo_settings[...]` /
`readout_*` dicts -> new `qubits[0].parameters.<attr>` ==
`TunableTransmonQubitParameters`, applied through `temporary_parameters`):

    qubit_parameters["ro_len"]         -> readout_length
    ro_len_test / ro_len / ro_len_sw   -> readout_length (pulse) and
                                         readout_integration_length (weighting)
    ro_amp_test / ro_amp_sw           -> readout_amplitude
    readout_pulse_test =
        pulse_library.const(uid=...,
            length=ro_len_test,
            amplitude=ro_amp_test)     -> readout_pulse = {'function': 'const'}
                                         (length/amplitude come from
                                          readout_length / readout_amplitude,
                                          so they are NOT repeated in the dict)
    readout_weighting_function_test =
        pulse_library.const(length=
            ro_len_test, amplitude=1)  -> readout_integration_length +
                                         readout_integration_kernels_type='default'
    lsg_q0["acquire_line"].port_delay
        / qubit_parameters["ro_int_delay"]
        / readout_delay / port_delay_sw-> readout_integration_delay
    qubit_parameters["relax"]          -> reset_delay_length
    readout_long_wait['relax_time']    -> reset_delay_length (long value, e.g. 500e-3)
    qubit_parameters["ro_freq_opt"]
        / 'measure_freq' / 'acquire_freq'
                                       -> readout_resonator_frequency (ABSOLUTE now:
                                          old ro_freq was an IF, absolute freq was
                                          lo_settings["ro_lo"] + ro_freq)
    lo_settings["ro_lo"]               -> readout_lo_frequency
    readout_test['readout_range'] /
        lsg_q0["measure_line"].range   -> readout_range_out (input: readout_range_in)
    readout_low / readout_opt /
        readout_test (dicts of pulses)  -> temporary_parameters[q.uid]
                                          (a deepcopy'd
                                           TunableTransmonQubitParameters);
                                          `readout_opt` in the new notebook
                                          (cell 100) is only a read-only summary
    x180                               -> qops.prepare_state(q, 'e') (state 'e')
    x180_ef                            -> qops.prepare_state(q, 'f') (state 'f')
    qubit_parameters['rabi_slope'] /
        qubit_parameters['rabi_intercept']
                                       -> ge_drive_amplitude_pi / ge_drive_length
                                          (the pi amplitude is now swept directly
                                           via temp_pars.ge_drive_amplitude_pi)
    pulse_length (gaussian_pulse)      -> ge_drive_length (+ ge_drive_pulse dict)
    n_average (= exponent)             -> n_avg_exponent, used as
                                          options.count(2**n_avg_exponent)
    n_av                               -> 2**n_avg_exponent
    qsample_params / sample_parameters  -> sample_name, qubit_name,
                                          cooldown_start_date, data_root_directory

Experiment/API level:

    create_rabi_SS(sweep_2, x180, readout_opt, n_average) /
    make_rabi_SS(...) + exp.set_signal_map(qubit_meas_map)
        + my_session.compile/run        -> iq_blobs.experiment_workflow(
                                              session=..., qpu=..., qubits=[uid],
                                              states='ge' | 'gef',
                                              temporary_parameters=...).run()
    make_two_point_sweep()             -> not needed: the two "points" are now the
                                          `states` calibration traces ('g' and 'e')
    create_SS(state, x180, x180_ef, ...)
        looped over states=['g','e','f'] -> a single workflow call with
                                          states='gef'
    AveragingMode.SINGLE_SHOT (manual) -> IQBlobExperimentOptions default
                                          (averaging_mode=SINGLE_SHOT)
    SS_results.get_data("SS_rabi")[:,0]-> result[dsl.handles.calibration_trace_handle(
                                              q.uid, 'g')].data
    SS_results.get_data("SS_rabi")[:,1]-> ... calibration_trace_handle(q.uid, 'e')
    SS_results.get_data("shots")       -> ... calibration_trace_handle(q.uid, state)
    SS_results.get_axis("SS_rabi")[0]  -> shot index (implicit: np.arange(len(shots)))
    SS_results.get_axis("SS_rabi")[1]  -> replaced by the state label
    zero_data / one_data / two_data    -> shots_per_state['g'/'e'/'f']
    analize_Single_Shots(...)          -> analyze_single_shots(...) (same maths,
                                          snake_case keys: 'distance', 'mean_0',
                                          'std_x_0', 'rel_std_0', ...)
    zero_data_proj / one_data_proj / r -> res_ss['shots_0_proj'] /
                                          res_ss['shots_1_proj'] /
                                          res_ss['distance']
    LinearDiscriminantAnalysis (manual,
        old cell 304) / compute_pca    -> iq_blobs analysis task `fit_data`
                                          (sklearn LDA) + `plot_iq_blobs`
                                          decision boundary
    (not present in old notebook)      -> assignment matrix / assignment fidelity
                                          from `calculate_assignment_matrices` and
                                          `calculate_assignment_fidelities`
    Rel_STD_0 minimisation over sweeps -> same, plus assignment fidelity as the
                                          preferred figure of merit
    get_path_to_file(...) + savemat    -> folder_store (automatic) + optional
                                          legacy .mat export via get_path_to_file()
    Data_SS.update(qubit_parameters._params)
        / Data_SS.update(lo_settings._params)
                                       -> attrs.asdict(qubit.parameters) filtered to
                                          scalars + sample_name / qubit_name /
                                          cooldown_start_date
    meas_ready() (playsound)            -> dropped (LoggingStore/FolderStore already
                                          report workflow completion)

REQUIRED IMPORT CHANGES
-------------------------------------------------------------------------------
notebook cell 5 (LabOne Q Libraries): add `iq_blobs` to the
`from laboneq_applications.experiments import (...)` list.

notebook cell 7 (Other Imports): add
    import pandas as pd
    from scipy.optimize import curve_fit
    from scipy.stats import norm
-------------------------------------------------------------------------------
"""

# %% [markdown]
# # Single Shot 0 and 1 Measurements

# %% [markdown]
# Single-shot (unaveraged) readout of the qubit prepared in g, e (and f).
#
# 1. **One Single Shot Measurement** — acquire the single shots for each prepared
#    state, classify them with a linear discriminant, and quantify the readout
#    with the state distance, the relative shot noise and the correct-state
#    assignment fidelity.
# 2. **Single Shot vs. Drive Pulse Length** — repeat the measurement for a range
#    of pi-pulse lengths (i.e. Rabi frequencies).
# 3. **Single Shot vs. Integration Length and Delay** — repeat the measurement
#    for a range of integration delays and integration lengths at a fixed
#    readout pulse.
# 4. **Single Shot vs. Readout Amplitude and Length** — repeat the measurement
#    for a range of readout amplitudes and readout lengths.
#
# The readout parameters optimized in `# Readout Optimization` are the starting
# point here; the best settings found below are written back into the QPU.

# %% [markdown]
# ## Helpers

# %%
# Helpers used by the single-shot cells.
# Replaces the old `analize_Single_Shots`, `gauss`/`bimodal`
# (lib/helpers/fitting_helper.py) and `compute_pca`.
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import norm

from laboneq_applications.experiments import iq_blobs  # add to cell 5 imports


def gauss(x, mu, sigma, A):
    """Old `lib.helpers.fitting_helper.gauss`, unchanged."""
    return A * np.exp(-((x - mu) ** 2) / 2 / sigma**2)


def bimodal(x, mu1, sigma1, A1, mu2, sigma2, A2):
    """Old `lib.helpers.fitting_helper.bimodal`, unchanged."""
    return gauss(x, mu1, sigma1, A1) + gauss(x, mu2, sigma2, A2)


def collect_shots_from_result(result, qubit_uid: str, states: str) -> dict:
    """Single shots per prepared state from an `iq_blobs` workflow result.

    New-structure replacement for the old
    `SS_results.get_data("SS_rabi")[:, 0]` / `[:, 1]` (two-point sweep) and
    `SS_results.get_data("shots")` (one experiment per state).
    """
    return {
        s: result[dsl.handles.calibration_trace_handle(qubit_uid, s)].data
        for s in states
    }


def analyze_single_shots(shots_per_state, state_0='g', state_1='e',
                         plot=False, n_bins=50):
    """Rotate the shots onto the state-discrimination axis and get its statistics.

    New-structure replacement for the old `analize_Single_Shots(SS_results)`.
    Same maths, but it takes the `shots_per_state` dict instead of a
    `Results` object, and returns snake_case keys plus the rotated/projected
    shots (old `zero_data_proj` / `one_data_proj`).

    After the rotation, state_0 sits on the negative and state_1 on the positive
    real axis, so `shots_0_proj > 0` counts the misassigned state_0 shots.
    """
    data_0 = np.asarray(shots_per_state[state_0])
    data_1 = np.asarray(shots_per_state[state_1])

    mean_0 = np.mean(data_0)
    mean_1 = np.mean(data_1)

    mid_point = 0.5 * (mean_0 + mean_1)

    data_0_corr = data_0 - mid_point
    data_1_corr = data_1 - mid_point

    # old: r = np.abs(zero_mean - one_mean) / 2
    distance = np.abs(mean_0 - mean_1) / 2
    phi = np.angle(mean_0 - mid_point)

    data_0_rot = data_0_corr * np.exp(1j * (np.pi - phi))
    data_1_rot = data_1_corr * np.exp(1j * (np.pi - phi))

    std_x_0 = np.sqrt(np.var(data_0_rot.real, ddof=1))
    std_y_0 = np.sqrt(np.var(data_0_rot.imag, ddof=1))
    std_x_1 = np.sqrt(np.var(data_1_rot.real, ddof=1))
    std_y_1 = np.sqrt(np.var(data_1_rot.imag, ddof=1))

    results = {
        'distance': distance,
        'mean_0': np.mean(data_0_rot),
        'mean_1': np.mean(data_1_rot),
        'std_x_0': std_x_0,
        'std_y_0': std_y_0,
        'std_x_1': std_x_1,
        'std_y_1': std_y_1,
        'rel_std_0': std_x_0 / distance,
        'rel_std_1': std_x_1 / distance,
        'shots_0_rot': data_0_rot,
        'shots_1_rot': data_1_rot,
        'shots_0_proj': data_0_rot.real,
        'shots_1_proj': data_1_rot.real,
        'n_misassigned_0': int(np.sum(data_0_rot.real > 0)),
        'n_assigned_0': int(np.sum(data_0_rot.real <= 0)),
    }

    if plot:
        fig, axs = plt.subplots(1, 2, sharey=True, tight_layout=True)
        fig.suptitle(f'Rotated single shots - {state_0} vs {state_1}')

        axs[0].set_title('Real')
        axs[0].hist(data_0_rot.real, bins=n_bins, alpha=0.5, label=state_0)
        axs[0].hist(data_1_rot.real, bins=n_bins, alpha=0.5, label=state_1)
        axs[0].set_yscale('log')
        axs[0].legend()

        axs[1].set_title('Imag')
        axs[1].hist(data_0_rot.imag, bins=n_bins, alpha=0.5, label=state_0)
        axs[1].hist(data_1_rot.imag, bins=n_bins, alpha=0.5, label=state_1)
        axs[1].set_yscale('log')
        axs[1].legend()

        results['figure'] = fig

    return results


def summarize_single_shot_metrics(res_ss, assignment_fidelity=None):
    """Compact printout of the figures of merit of one single-shot measurement."""
    print('State distance:          ', round(float(res_ss['distance']), 6))
    print('Relative STD state 0:    ', round(float(res_ss['rel_std_0']), 4))
    print('Relative STD state 1:    ', round(float(res_ss['rel_std_1']), 4))
    print('Misassigned state-0 shots:', res_ss['n_misassigned_0'],
          '/', res_ss['n_misassigned_0'] + res_ss['n_assigned_0'])
    if assignment_fidelity is not None:
        print('Assignment fidelity:     ', f'{assignment_fidelity * 100:0.2f} %')


# %% [markdown]
# ## One Single Shot Measurement

# %% [markdown]
# #### Experiment Parameters

# %%
update_global_parameters = True

# old: states = ['g', 'e', 'f'] looped over create_SS(state, ...)
states = 'gef'

# old: n_average = 17  ->  2**17 = 131072 single shots per state
n_avg_exponent = 17

# Readout settings for the single shots.
# old: ro_len_test = 1e-6, ro_amp_test = 0.55, readout_test = {...},
#      readout_long_wait['relax_time'] = 500e-3
readout_length = 1e-6
readout_integration_length = 1e-6
readout_amplitude = 0.55
readout_integration_delay = 80e-9
readout_range_out = -20
readout_range_in = -35
# old: qubit_parameters["relax"] / readout_long_wait['relax_time'].
# Use a long value only if you want to see the thermal population;
# 500e-3 makes 2**17 shots per state extremely slow.
reset_delay_length = 150e-6

# old: pulse_library.const(uid="readout_pulse", length=ro_len_test,
#                          amplitude=ro_amp_test)
# length and amplitude come from readout_length / readout_amplitude.
readout_pulse = {
    'function': 'const',
}

qubit_to_measure = qubits[0]

temporary_parameters = {}
temp_pars = deepcopy(qubits[0].parameters)
temp_pars.readout_amplitude = readout_amplitude
temp_pars.readout_length = readout_length
temp_pars.readout_pulse = readout_pulse
temp_pars.readout_integration_length = readout_integration_length
temp_pars.readout_integration_delay = readout_integration_delay
temp_pars.readout_range_out = readout_range_out
temp_pars.readout_range_in = readout_range_in
temp_pars.reset_delay_length = reset_delay_length
temporary_parameters[qubit_to_measure.uid] = temp_pars

# old: print('Measure lenght', qubit_parameters["ro_len"])
#      print('Aq port delay', lsg_q0["acquire_line"].port_delay)
print('Readout length:             ', temp_pars.readout_length)
print('Readout integration length: ', temp_pars.readout_integration_length)
print('Readout integration delay:  ', temp_pars.readout_integration_delay)
print('Readout amplitude:          ', temp_pars.readout_amplitude)
print('Reset delay length:         ', temp_pars.reset_delay_length)
print('Readout resonator frequency:', temp_pars.readout_resonator_frequency)
print('Number of shots per state:  ', 2**n_avg_exponent)

# %% [markdown]
# #### Run Workflow

# %%
# old: for state in states: create_SS(state, x180, x180_ef, readout_opt, n_average)
#      -> my_session.compile / my_session.run, then result.get_data("shots")
options = iq_blobs.experiment_workflow.options()
options.count(2**n_avg_exponent)
options.close_figures(False)
# the analysis classifies the shots with sklearn LinearDiscriminantAnalysis,
# replacing the manual LDA/PCA cells of the old notebook.
options.do_analysis(True)

exp_workflow = iq_blobs.experiment_workflow(
    session=session,
    qpu=qpu,
    qubits=[qubit_to_measure.uid],
    states=states,
    options=options,
    temporary_parameters=temporary_parameters,
)
workflow_result = exp_workflow.run()

# %% [markdown]
# #### Analysis Plots

# %%
# old: zero_data = result_arr[0,:], one_data = result_arr[1,:], two_data = result_arr[2,:]
result = workflow_result.output
shots_per_state = collect_shots_from_result(result, qubit_to_measure.uid, states)

# convenience aliases matching the old variable names
zero_data = shots_per_state['g']
one_data = shots_per_state['e']
two_data = shots_per_state.get('f')

shots_arr = np.array([shots_per_state[s] for s in states])
print('Shots array shape (states, shots):', shots_arr.shape)

state_labels = {'g': 'ground', 'e': 'first excited', 'f': 'second excited'}
state_colors = {'g': 'b', 'e': 'r', 'f': 'y'}
state_alphas = {'g': 0.1, 'e': 0.1, 'f': 0.01}

# %%
# old cell 292: plot measurement data on IQ, plus the state means
fig, ax = plt.subplots()
ax.set_title(f'Single shots on the IQ plane - {qubit_to_measure.uid}')
for s in states:
    data = shots_per_state[s]
    ax.plot(data.real, data.imag, '.', color=state_colors[s],
            alpha=state_alphas[s], label=state_labels[s])
for s in states:
    data = shots_per_state[s]
    ax.plot(np.mean(data.real), np.mean(data.imag), 'o',
            mfc=state_colors[s], mec='k')
ax.set_xlabel('Real part, a.u.')
ax.set_ylabel('Imaginary part, a.u.')
ax.legend()

# old: plt.xlim(-0.1, 0.12); plt.ylim(-0.25, 0.05) - set manually if needed
# ax.set_xlim(-0.1, 0.12)
# ax.set_ylim(-0.25, 0.05)

figname = 'Single_shot_points_'
file_path = get_path_to_file(figname, '.png')
fig.savefig(file_path, dpi=600, format='png', bbox_inches='tight')

# %%
# old cell 293/294: analize_Single_Shots(SS_results, plot=True)
res_ss = analyze_single_shots(shots_per_state, state_0='g', state_1='e', plot=True)

# assignment matrix / fidelity are new: they come from the iq_blobs analysis
assignment_fidelities = workflow_result.tasks['analysis_workflow'].output
assignment_matrices = get_analysis_task_output(
    workflow_result, 'calculate_assignment_matrices'
)
assignment_fidelity = assignment_fidelities.get(qubit_to_measure.uid)

summarize_single_shot_metrics(res_ss, assignment_fidelity)
pprint({k: v for k, v in res_ss.items()
        if not isinstance(v, np.ndarray) and k != 'figure'})

# %%
# old cell 297: plot the raw (unrotated) distributions
n_bins = 50

fig, axs = plt.subplots(1, 2, sharey=True, tight_layout=True)
fig.suptitle(f'Single-shot distributions - {qubit_to_measure.uid}')

axs[0].set_title('Real')
axs[1].set_title('Imag')
for s in states:
    data = shots_per_state[s]
    axs[0].hist(data.real, bins=n_bins, alpha=0.5, label=state_labels[s])
    axs[1].hist(data.imag, bins=n_bins, alpha=0.5, label=state_labels[s])
axs[0].legend()
axs[1].legend()

figname = 'Single_shot_hist_'
file_path = get_path_to_file(figname, '.png')
fig.savefig(file_path, dpi=600, format='png', bbox_inches='tight')

# %%
# old cell 298: relative-distance histogram of the projected shots
# old: zero_data_proj / one_data_proj / r
zero_data_proj = res_ss['shots_0_proj']
one_data_proj = res_ss['shots_1_proj']
r = res_ss['distance']

n_bins = 200

fig, ax = plt.subplots()
ax.set_title(f'Projected single shots - {qubit_to_measure.uid}')
ax.hist(zero_data_proj / r, bins=n_bins, alpha=0.5, label=state_labels['g'])
ax.hist(one_data_proj / r, bins=n_bins, alpha=0.5, label=state_labels['e'])
ax.axvline(1, color='k', ls='--')
ax.axvline(-1, color='k', ls='--')
ax.set_yscale('log')
ax.set_ylabel('N points')
ax.set_xlabel('Relative distance')
ax.legend()

# %%
# old cell 299: single Gaussian fit of the projected state-0 shots
data = zero_data_proj / r

fig, ax = plt.subplots()
n, bins, patches = ax.hist(data, bins=n_bins, alpha=0.5, density=True)

(mu, sigma) = norm.fit(data)

# add a 'best fit' line
y = norm.pdf(bins, mu, sigma)
ax.plot(bins, y, 'r--', linewidth=2)
ax.set_yscale('log')
ax.set_ylabel('Probability density')
ax.set_xlabel('Relative distance')
ax.set_title(f'Gaussian fit state 0: mu = {mu:.4f}, sigma = {sigma:.4f}')
print('mu:', mu, ' sigma:', sigma)

# %%
# old cell 300: bimodal fit of the projected state-1 shots -> residual ground pop.
data = one_data_proj / r

fig, ax = plt.subplots()
y, x, patches = ax.hist(data, bins=n_bins, color='red', alpha=0.25)
x = (x[1:] + x[:-1]) / 2

expected = (-1, .2, 1050, 1, .2, 125)
params, cov = curve_fit(bimodal, x, y, expected)
sigma = np.sqrt(np.diag(cov))
x_fit = np.linspace(x.min(), x.max(), 500)
# plot combined...
ax.plot(x_fit, bimodal(x_fit, *params), color='green', lw=3, label='One+Zero')
# ...and individual Gauss curves
ax.plot(x_fit, gauss(x_fit, *params[:3]), color='red', lw=2, ls='--', label='One')
ax.plot(x_fit, gauss(x_fit, *params[3:]), color='b', lw=2, ls=':', label='Zero')
ax.set_yscale('log')
ax.set_ylabel('N points')
ax.set_xlabel('Relative distance')
ax.set_ylim(1e-1, 5e3)
ax.set_title(f'Bimodal fit state 1 - {qubit_to_measure.uid}')
ax.legend()
print(pd.DataFrame(data={'params': params, 'sigma': sigma},
                   index=bimodal.__code__.co_varnames[1:]))
plt.show()

print('Area ratio:', params[4] * params[5] / (params[1] * params[2]))

# %%
# old cell 301: bimodal fit of the projected state-0 shots -> residual excited pop.
data = zero_data_proj / r

fig, ax = plt.subplots()
y, x, patches = ax.hist(data, bins=n_bins, color='blue', alpha=0.25)
x = (x[1:] + x[:-1]) / 2

expected = (-1.5, 1.0, 250, 1, 1.0, 2025)
params, cov = curve_fit(bimodal, x, y, expected)
sigma = np.sqrt(np.diag(cov))
x_fit = np.linspace(x.min(), x.max(), 500)
# plot combined...
ax.plot(x_fit, bimodal(x_fit, *params), color='green', lw=3, label='One+Zero')
# ...and individual Gauss curves
ax.plot(x_fit, gauss(x_fit, *params[:3]), color='red', lw=2, ls='--', label='One')
ax.plot(x_fit, gauss(x_fit, *params[3:]), color='blue', lw=2, ls=':', label='Zero')
ax.set_yscale('log')
ax.set_ylabel('N points')
ax.set_xlabel('Relative distance')
ax.set_ylim(1e-1, 5e3)
ax.set_title(f'Bimodal fit state 0 - {qubit_to_measure.uid}')
ax.legend()
print(pd.DataFrame(data={'params': params, 'sigma': sigma},
                   index=bimodal.__code__.co_varnames[1:]))
plt.show()

print('Area ratio:', params[1] * params[2] / (params[4] * params[5]))

# %%
# old cell 305: 2D histogram of the shots
n_bins = 50

fig, ax = plt.subplots(tight_layout=True)
ax.set_title(f'Single-shot density - {qubit_to_measure.uid}')
ax.hist2d(zero_data.real, zero_data.imag, n_bins)
ax.hist2d(one_data.real, one_data.imag, n_bins)
ax.set_xlabel('Real part, a.u.')
ax.set_ylabel('Imaginary part, a.u.')

# %%
# New: the assignment matrix produced by the iq_blobs analysis replaces the manual
# LinearDiscriminantAnalysis / compute_pca cells (old cells 302-304).
if qubit_to_measure.uid in assignment_matrices:
    print('Correct-state-assignment matrix:')
    print(np.round(assignment_matrices[qubit_to_measure.uid], 4))
    print('Assignment fidelity:', f'{assignment_fidelity * 100:0.2f} %')

# %% [markdown]
# #### Update Parameters

# %%
# old cell 286: Data_SS = {...}; Data_SS.update(qubit_parameters._params);
#               savemat(get_path_to_file('Single_shots_all_unsh_', '.mat'), Data_SS)
data_ss = {f'shots_{s}': shots_per_state[s] for s in states}
data_ss['states'] = list(states)
data_ss['shot_index'] = np.arange(shots_arr.shape[-1])
data_ss['n_shots'] = 2**n_avg_exponent
data_ss.update({k: v for k, v in res_ss.items()
                if isinstance(v, (int, float, complex))})
if qubit_to_measure.uid in assignment_matrices:
    data_ss['assignment_matrix'] = assignment_matrices[qubit_to_measure.uid]
    data_ss['assignment_fidelity'] = assignment_fidelity

data_ss.update(
    {k: v for k, v in attrs.asdict(temporary_parameters[qubit_to_measure.uid]).items()
     if isinstance(v, (int, float, str))}
)
data_ss['sample_name'] = sample_name
data_ss['qubit_name'] = qubit_name
data_ss['cooldown_start_date'] = cooldown_start_date

file_path = get_path_to_file('Single_shots_all_unsh_', '.mat')
savemat(file_path, data_ss)
print(f'Saved single shots to: {file_path}')

# %%
if update_global_parameters:
    qubit_to_measure.parameters = deepcopy(temporary_parameters[qubit_to_measure.uid])
    save(qpu, qpu_file_path)
    print('Updated global experiment parameters!\n')

print('Readout amplitude: ', qubit_to_measure.parameters.readout_amplitude)
print('Readout length: ', qubit_to_measure.parameters.readout_length)
print('Readout integration length: ',
      qubit_to_measure.parameters.readout_integration_length)
print('Readout integration delay: ',
      qubit_to_measure.parameters.readout_integration_delay)
print('Reset delay length: ', qubit_to_measure.parameters.reset_delay_length)

# %% [markdown]
# ## Single Shot Measurement for Different Rabi Frequencies

# %% [markdown]
# #### Experiment Parameters

# %%
update_global_parameters = False

# old: n_average = 17
n_avg_exponent = 15  # reduce: this is a sweep over 36 pi-pulse lengths

states = 'ge'

# old: pulse_length = np.linspace(60e-9, 400e-9, 36); rabi_freq = 1/pulse_length
#      pi_amp = qubit_parameters['rabi_slope']*rabi_freq*1e-6
#                + qubit_parameters['rabi_intercept']
drive_length_arr = np.linspace(60e-9, 400e-9, 36)
rabi_freq_arr = 1 / drive_length_arr

# old: gaussian_pulse = pulse_library.gaussian(uid=..., length=pulse_length[i],
#                                              amplitude=1.0)
ge_drive_pulse = {
    'function': 'gaussian',
    'sigma': 0.25,
}

# The old notebook extrapolated the pi amplitude from a linear
# rabi_slope / rabi_intercept calibration. With the workflow structure the pi
# amplitude for the *current* drive length is a qubit parameter, so scale it
# instead of re-deriving it (or set `ge_drive_amplitude_pi_arr` manually).
rabi_slope = qubit_to_measure.parameters.ge_drive_amplitude_pi * \
    qubit_to_measure.parameters.ge_drive_length
ge_drive_amplitude_pi_arr = np.clip(rabi_slope / drive_length_arr, 0.0, 1.0)

print(pd.DataFrame({
    'ge_drive_length': drive_length_arr,
    'rabi_freq_MHz': rabi_freq_arr * 1e-6,
    'ge_drive_amplitude_pi': ge_drive_amplitude_pi_arr,
}))

qubit_to_measure = qubits[0]

# %% [markdown]
# #### Run Workflow

# %%
# old: for i in range(len(pulse_length)): make_rabi_SS(...) -> compile/run ->
#      rabi_SS_sweep_list.append(results_SS.get_data("SS_rabi"))
options = iq_blobs.experiment_workflow.options()
options.count(2**n_avg_exponent)
options.close_figures(True)  # one IQ-blob figure per drive length
options.do_analysis(True)

ss_drive_length_sweep_shots = []
ss_drive_length_sweep_metrics = []
ss_drive_length_sweep_fidelities = []

for drive_length, drive_amplitude_pi in zip(drive_length_arr,
                                            ge_drive_amplitude_pi_arr):
    print('Drive length:', round(drive_length * 1e9, 3), 'ns',
          '| pi amplitude:', round(float(drive_amplitude_pi), 5))

    temporary_parameters = {}
    temp_pars = deepcopy(qubit_to_measure.parameters)
    temp_pars.ge_drive_length = float(drive_length)
    temp_pars.ge_drive_amplitude_pi = float(drive_amplitude_pi)
    temp_pars.ge_drive_pulse = ge_drive_pulse
    temporary_parameters[qubit_to_measure.uid] = temp_pars

    exp_workflow = iq_blobs.experiment_workflow(
        session=session,
        qpu=qpu,
        qubits=[qubit_to_measure.uid],
        states=states,
        options=options,
        temporary_parameters=temporary_parameters,
    )
    workflow_result = exp_workflow.run()

    shots = collect_shots_from_result(
        workflow_result.output, qubit_to_measure.uid, states
    )
    ss_drive_length_sweep_shots.append(np.array([shots[s] for s in states]))

    res = analyze_single_shots(shots, state_0='g', state_1='e', plot=False)
    ss_drive_length_sweep_metrics.append(
        {k: v for k, v in res.items() if isinstance(v, (int, float, complex))}
    )
    ss_drive_length_sweep_fidelities.append(
        workflow_result.tasks['analysis_workflow'].output.get(
            qubit_to_measure.uid, np.nan
        )
    )

ss_drive_length_sweep_arr = np.array(ss_drive_length_sweep_shots)
print('Sweep array shape (drive lengths, states, shots):',
      ss_drive_length_sweep_arr.shape)

# %% [markdown]
# #### Analysis Plots

# %%
rel_std_0_arr = np.array([m['rel_std_0'] for m in ss_drive_length_sweep_metrics])
fidelity_arr = np.array(ss_drive_length_sweep_fidelities, dtype=float)

optimal_index = int(np.nanargmin(rel_std_0_arr))
print('Best drive length:', round(drive_length_arr[optimal_index] * 1e9, 3), 'ns',
      '| Rabi frequency:', round(rabi_freq_arr[optimal_index] * 1e-6, 3), 'MHz',
      '| rel_std_0:', round(float(rel_std_0_arr[optimal_index]), 4))

fig, ax = plt.subplots(2, 1, sharex=True, figsize=(10, 8))
fig.suptitle(f'Single shot vs. Rabi frequency - {qubit_to_measure.uid}', fontsize=16)
fig.supxlabel('Rabi frequency, MHz')

ax[0].plot(rabi_freq_arr * 1e-6, rel_std_0_arr, '.k')
ax[0].set_ylabel('Relative STD state 0')
ax[0].set_yscale('log')

ax[1].plot(rabi_freq_arr * 1e-6, fidelity_arr * 100, '.k')
ax[1].set_ylabel('Assignment fidelity, %')

for axis in ax:
    axis.axvline(x=rabi_freq_arr[optimal_index] * 1e-6, ls='-.', color='r',
                 label='optimal')
    axis.legend()

file_path = get_path_to_file('Single_shots_vs_rabi_freq_', '.png')
fig.savefig(file_path, dpi=600, format='png', bbox_inches='tight')

# %% [markdown]
# #### Update Parameters

# %%
# old cell 310: savemat('Single_shots_0_pi_diff_pipulses_', ...)
data_ss = {
    'ss_drive_length_sweep_arr': ss_drive_length_sweep_arr,
    'states': list(states),
    'ge_drive_length': drive_length_arr,
    'rabi_freq': rabi_freq_arr,
    'ge_drive_amplitude_pi': ge_drive_amplitude_pi_arr,
    'rel_std_0': rel_std_0_arr,
    'assignment_fidelity': fidelity_arr,
    'n_shots': 2**n_avg_exponent,
    'comment': 'Sweep of the pi-pulse length, array dim [drive_length, state, shot]',
}
data_ss.update(
    {k: v for k, v in attrs.asdict(qubit_to_measure.parameters).items()
     if isinstance(v, (int, float, str))}
)
data_ss['sample_name'] = sample_name
data_ss['qubit_name'] = qubit_name
data_ss['cooldown_start_date'] = cooldown_start_date

file_path = get_path_to_file('Single_shots_0_pi_diff_pipulses_', '.mat')
savemat(file_path, data_ss)
print(f'Saved drive-length sweep to: {file_path}')

# %%
if update_global_parameters:
    temp_pars = deepcopy(qubit_to_measure.parameters)
    temp_pars.ge_drive_length = float(drive_length_arr[optimal_index])
    temp_pars.ge_drive_amplitude_pi = float(ge_drive_amplitude_pi_arr[optimal_index])
    temp_pars.ge_drive_pulse = ge_drive_pulse
    qubit_to_measure.parameters = temp_pars
    save(qpu, qpu_file_path)
    print('Updated global experiment parameters!\n')

print('ge drive length: ', qubit_to_measure.parameters.ge_drive_length)
print('ge drive amplitude pi: ', qubit_to_measure.parameters.ge_drive_amplitude_pi)

# %% [markdown]
# ## Single Shot Measurement for Different Integration Lengths and Delays

# %% [markdown]
# #### Experiment Parameters

# %%
update_global_parameters = True

# old: n_average = 17
n_avg_exponent = 15

states = 'ge'

# old: print('Measure lenght', readout_pulse.length)
#      print('Aq port delay', lsg_q0["acquire_line"].port_delay)
print('Readout length:            ', qubit_to_measure.parameters.readout_length)
print('Readout integration length:',
      qubit_to_measure.parameters.readout_integration_length)
print('Readout integration delay: ',
      qubit_to_measure.parameters.readout_integration_delay)

# Here the readout pulse amplitude and length are fixed and we vary the
# integration delay and integration (weighting) length.
# old: port_delay_sw = np.linspace(380, 400, 5)*1e-9
#      ro_len = [readout_pulse.length]  (weighting function length)
readout_length = qubit_to_measure.parameters.readout_length
readout_integration_delay_arr = np.linspace(60, 100, 5) * 1e-9
readout_integration_length_arr = np.array([readout_length])
# to sweep the integration length as well (old commented-out line
# `ro_len = np.arange(100, 2100 - port_delay_sw[k], 100)*1e-9`):
# readout_integration_length_arr = np.arange(100, 2100, 200) * 1e-9

qubit_to_measure = qubits[0]

# %% [markdown]
# #### Run Workflow

# %%
# old cell 314: nested loop over port_delay_sw / ro_len -> make_rabi_SS ->
#               analize_Single_Shots(results_SS, plot=False)
options = iq_blobs.experiment_workflow.options()
options.count(2**n_avg_exponent)
options.close_figures(True)
options.do_analysis(False)  # only the projected statistics are needed here

ss_delay_sweep_metrics = []
ss_delay_sweep_shots = []

for integration_delay in readout_integration_delay_arr:
    print('Integration delay:', round(integration_delay * 1e9, 3), 'ns')

    metrics_inner = []
    shots_inner = []

    for integration_length in readout_integration_length_arr:
        print('  Integration length:', round(integration_length * 1e9, 3), 'ns')

        temporary_parameters = {}
        temp_pars = deepcopy(qubit_to_measure.parameters)
        temp_pars.readout_length = readout_length
        temp_pars.readout_integration_delay = float(integration_delay)
        temp_pars.readout_integration_length = float(integration_length)
        temporary_parameters[qubit_to_measure.uid] = temp_pars

        exp_workflow = iq_blobs.experiment_workflow(
            session=session,
            qpu=qpu,
            qubits=[qubit_to_measure.uid],
            states=states,
            options=options,
            temporary_parameters=temporary_parameters,
        )
        workflow_result = exp_workflow.run()

        shots = collect_shots_from_result(
            workflow_result.output, qubit_to_measure.uid, states
        )
        shots_inner.append(np.array([shots[s] for s in states]))

        res = analyze_single_shots(shots, state_0='g', state_1='e', plot=False)
        metrics_inner.append(
            {k: v for k, v in res.items() if isinstance(v, (int, float, complex))}
        )

    ss_delay_sweep_metrics.append(metrics_inner)
    ss_delay_sweep_shots.append(shots_inner)

ss_delay_sweep_arr = np.array(ss_delay_sweep_shots)
print('Sweep array shape (delays, integration lengths, states, shots):',
      ss_delay_sweep_arr.shape)

# %% [markdown]
# #### Analysis Plots

# %%
# old cell 317: min / argmin of Rel_STD_0 over the nested sweep
min_val = []
argmin_val = []

for metrics_inner in ss_delay_sweep_metrics:
    rel_std_0 = np.array([m['rel_std_0'] for m in metrics_inner])
    min_val.append(np.nanmin(rel_std_0))
    argmin_val.append(int(np.nanargmin(rel_std_0)))

optimal_delay_index = int(np.nanargmin(np.array(min_val)))
optimal_length_index = argmin_val[optimal_delay_index]

readout_integration_delay_opt = float(
    readout_integration_delay_arr[optimal_delay_index]
)
readout_integration_length_opt = float(
    readout_integration_length_arr[optimal_length_index]
)

print('Readout length is', readout_length)
print('Minimal relative error value is', np.round(min_val[optimal_delay_index], 3),
      'for delay', np.round(readout_integration_delay_opt * 1e9, 3),
      'ns (index', optimal_delay_index, ') and integration length',
      readout_integration_length_opt, '(index', optimal_length_index, ').')
if 0 < optimal_delay_index < len(readout_integration_delay_arr) - 1:
    print('Optimal integration delay is between',
          np.round(readout_integration_delay_arr[optimal_delay_index - 1] * 1e9, 3),
          'and',
          np.round(readout_integration_delay_arr[optimal_delay_index + 1] * 1e9, 3),
          'ns')

rel_std_0_arr = np.array(
    [[m['rel_std_0'] for m in metrics_inner]
     for metrics_inner in ss_delay_sweep_metrics]
)

fig, ax = plt.subplots(figsize=(10, 5))
ax.set_title(f'Single shot vs. integration delay - {qubit_to_measure.uid}')
for k, integration_length in enumerate(readout_integration_length_arr):
    ax.plot(readout_integration_delay_arr * 1e9, rel_std_0_arr[:, k], '.-',
            label=f'{integration_length * 1e9:.0f} ns')
ax.axvline(x=readout_integration_delay_opt * 1e9, ls='-.', color='r', label='optimal')
ax.set_xlabel('Readout integration delay, ns')
ax.set_ylabel('Relative STD state 0')
ax.set_yscale('log')
ax.legend(title='Integration length')

file_path = get_path_to_file('Single_shots_vs_delay_and_int_len_', '.png')
fig.savefig(file_path, dpi=600, format='png', bbox_inches='tight')

# %% [markdown]
# #### Update Parameters

# %%
# old cell 319: lsg_q0["acquire_line"].port_delay = 3.8e-7
# set to a value != None to override the values extracted above.
manual_readout_integration_delay = None
manual_readout_integration_length = None
if manual_readout_integration_delay is not None:
    readout_integration_delay_opt = float(manual_readout_integration_delay)
if manual_readout_integration_length is not None:
    readout_integration_length_opt = float(manual_readout_integration_length)

if update_global_parameters:
    temp_pars = deepcopy(qubit_to_measure.parameters)
    temp_pars.readout_integration_delay = readout_integration_delay_opt
    temp_pars.readout_integration_length = readout_integration_length_opt
    qubit_to_measure.parameters = temp_pars
    save(qpu, qpu_file_path)
    print('Updated global experiment parameters!\n')

print('Readout integration delay: ',
      qubit_to_measure.parameters.readout_integration_delay)
print('Readout integration length: ',
      qubit_to_measure.parameters.readout_integration_length)

# %%
# old cell 327: savemat('Single_shots_0_pi_sweep_delay_and_ro_len_', ...)
data_ss = {
    'ss_delay_sweep_arr': ss_delay_sweep_arr,
    'states': list(states),
    'readout_integration_delay_sweep': readout_integration_delay_arr,
    'readout_integration_length_sweep': readout_integration_length_arr,
    'readout_length': readout_length,
    'rel_std_0': rel_std_0_arr,
    'n_shots': 2**n_avg_exponent,
    'comment': ('Sweep integration delay and integration length, array dim '
                '[delay, integration_length, state, shot]'),
}
data_ss.update(
    {k: v for k, v in attrs.asdict(qubit_to_measure.parameters).items()
     if isinstance(v, (int, float, str))}
)
data_ss['sample_name'] = sample_name
data_ss['qubit_name'] = qubit_name
data_ss['cooldown_start_date'] = cooldown_start_date

file_path = get_path_to_file('Single_shots_0_pi_sweep_delay_and_ro_len_', '.mat')
savemat(file_path, data_ss)
print(f'Saved delay/integration-length sweep to: {file_path}')

# %% [markdown]
# ## Single Shot Measurement for Different Readout Amplitudes and Lengths

# %% [markdown]
# #### Experiment Parameters

# %%
update_global_parameters = True

# old: n_average = 17
n_avg_exponent = 14

states = 'ge'

# Sweep power and length of the readout pulse. The integration delay is fixed
# and the integration window is equal to the readout pulse length.
# old: ro_amp_sw = np.linspace(0.05, 0.8, 21)
#      ro_len_sw = np.linspace(100, 2000, 10)*1e-9
readout_amplitude_arr = np.linspace(0.05, 0.8, 21)
readout_length_arr = np.linspace(100, 2000, 10) * 1e-9

readout_integration_delay = qubit_to_measure.parameters.readout_integration_delay

qubit_to_measure = qubits[0]

# %% [markdown]
# #### Run Workflow

# %%
# old cell 320: nested loop over ro_amp_sw / ro_len_sw -> make_rabi_SS ->
#               analize_Single_Shots(results_SS, plot=False)
options = iq_blobs.experiment_workflow.options()
options.count(2**n_avg_exponent)
options.close_figures(True)
options.do_analysis(False)

ss_ro_sweep_metrics = []

for readout_amplitude in readout_amplitude_arr:
    print('Readout amplitude:', round(float(readout_amplitude), 5))

    metrics_inner = []

    for readout_length in readout_length_arr:
        print('  Readout length:', round(readout_length * 1e9, 3), 'ns')

        temporary_parameters = {}
        temp_pars = deepcopy(qubit_to_measure.parameters)
        temp_pars.readout_amplitude = float(readout_amplitude)
        temp_pars.readout_length = float(readout_length)
        # old: readout_weighting_function_i = pulse_library.const(length=ro_len_sw[i])
        temp_pars.readout_integration_length = float(readout_length)
        temp_pars.readout_integration_delay = readout_integration_delay
        temporary_parameters[qubit_to_measure.uid] = temp_pars

        exp_workflow = iq_blobs.experiment_workflow(
            session=session,
            qpu=qpu,
            qubits=[qubit_to_measure.uid],
            states=states,
            options=options,
            temporary_parameters=temporary_parameters,
        )
        workflow_result = exp_workflow.run()

        shots = collect_shots_from_result(
            workflow_result.output, qubit_to_measure.uid, states
        )
        res = analyze_single_shots(shots, state_0='g', state_1='e', plot=False)
        metrics_inner.append(
            {k: v for k, v in res.items() if isinstance(v, (int, float, complex))}
        )

    ss_ro_sweep_metrics.append(metrics_inner)

# %% [markdown]
# #### Analysis Plots

# %%
# old cells 321/323: min / argmin of Rel_STD_0 and the Rel_STD_0 vs. amplitude plot
rel_std_0_arr = np.array(
    [[m['rel_std_0'] for m in metrics_inner] for metrics_inner in ss_ro_sweep_metrics]
)

optimal_amp_index = int(np.nanargmin(np.nanmin(rel_std_0_arr, axis=1)))
optimal_len_index = int(np.nanargmin(rel_std_0_arr[optimal_amp_index, :]))

readout_amplitude_opt = float(readout_amplitude_arr[optimal_amp_index])
readout_length_opt = float(readout_length_arr[optimal_len_index])

print('Minimal relative error value is',
      np.round(rel_std_0_arr[optimal_amp_index, optimal_len_index], 3),
      'for amplitude', np.round(readout_amplitude_opt, 3),
      '(index', optimal_amp_index, ') and length', readout_length_opt,
      '(index', optimal_len_index, ').')

fig, ax = plt.subplots(figsize=(10, 5))
ax.set_title(f'Single shot vs. readout amplitude - {qubit_to_measure.uid}')
for k, readout_length in enumerate(readout_length_arr):
    ax.plot(readout_amplitude_arr, rel_std_0_arr[:, k], '.-',
            label=f'{readout_length * 1e9:.0f} ns')
ax.axvline(x=readout_amplitude_opt, ls='-.', color='r', label='optimal')
ax.set_xlabel('Readout amplitude, a.u.')
ax.set_ylabel('Relative STD state 0')
ax.set_yscale('log')
ax.legend(title='Readout length', ncol=2)

file_path = get_path_to_file('Single_shots_vs_ro_amp_and_ro_len_', '.png')
fig.savefig(file_path, dpi=600, format='png', bbox_inches='tight')

# %%
fig, ax = plt.subplots(figsize=(10, 5))
ax.set_title(f'Relative STD state 0 - {qubit_to_measure.uid}')
im = ax.pcolormesh(readout_length_arr * 1e9, readout_amplitude_arr, rel_std_0_arr,
                   shading='nearest')
cb = fig.colorbar(im)
cb.set_label('Relative STD state 0')
ax.plot(readout_length_opt * 1e9, readout_amplitude_opt, 'rx', ms=12, label='optimal')
ax.set_xlabel('Readout length, ns')
ax.set_ylabel('Readout amplitude, a.u.')
ax.legend()

file_path = get_path_to_file('Single_shots_ro_amp_ro_len_map_', '.png')
fig.savefig(file_path, dpi=600, format='png', bbox_inches='tight')

# %% [markdown]
# #### Update Parameters

# %%
# set to a value != None to override the values extracted above.
manual_readout_amplitude = None
manual_readout_length = None
if manual_readout_amplitude is not None:
    readout_amplitude_opt = float(manual_readout_amplitude)
if manual_readout_length is not None:
    readout_length_opt = float(manual_readout_length)

if update_global_parameters:
    temp_pars = deepcopy(qubit_to_measure.parameters)
    temp_pars.readout_amplitude = readout_amplitude_opt
    temp_pars.readout_length = readout_length_opt
    temp_pars.readout_integration_length = readout_length_opt
    qubit_to_measure.parameters = temp_pars
    save(qpu, qpu_file_path)
    print('Updated global experiment parameters!\n')

print('Readout amplitude: ', qubit_to_measure.parameters.readout_amplitude)
print('Readout length: ', qubit_to_measure.parameters.readout_length)
print('Readout integration length: ',
      qubit_to_measure.parameters.readout_integration_length)

# %%
data_ss = {
    'states': list(states),
    'readout_amplitude_sweep': readout_amplitude_arr,
    'readout_length_sweep': readout_length_arr,
    'readout_integration_delay': readout_integration_delay,
    'rel_std_0': rel_std_0_arr,
    'n_shots': 2**n_avg_exponent,
    'comment': ('Sweep readout amplitude and readout length, array dim '
                '[readout_amplitude, readout_length]'),
}
data_ss.update(
    {k: v for k, v in attrs.asdict(qubit_to_measure.parameters).items()
     if isinstance(v, (int, float, str))}
)
data_ss['sample_name'] = sample_name
data_ss['qubit_name'] = qubit_name
data_ss['cooldown_start_date'] = cooldown_start_date

file_path = get_path_to_file('Single_shots_0_pi_sweep_ro_amp_and_ro_len_', '.mat')
savemat(file_path, data_ss)
print(f'Saved readout amplitude/length sweep to: {file_path}')

# %%
readout_opt = {
    'readout_amplitude': qubit_to_measure.parameters.readout_amplitude,
    'readout_length': qubit_to_measure.parameters.readout_length,
    'readout_pulse': qubit_to_measure.parameters.readout_pulse,
    'readout_integration_length': qubit_to_measure.parameters.readout_integration_length,
    'readout_integration_delay': qubit_to_measure.parameters.readout_integration_delay,
    'readout_integration_kernels_type':
        qubit_to_measure.parameters.readout_integration_kernels_type,
    'readout_resonator_frequency': qubit_to_measure.parameters.readout_resonator_frequency,
    'readout_lo_frequency': qubit_to_measure.parameters.readout_lo_frequency,
    'readout_range_out': qubit_to_measure.parameters.readout_range_out,
    'readout_range_in': qubit_to_measure.parameters.readout_range_in,
    'reset_delay_length': qubit_to_measure.parameters.reset_delay_length,
}
pprint(readout_opt)

# %%
qpu.quantum_elements
