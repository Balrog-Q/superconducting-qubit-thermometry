# New implementation of the "Single Shot 0 and 1 Measurements" notebook
# section.
#
# This file is written in the jupytext "percent" format: every `# %%` (or
# `# %% [markdown]`) marker starts a new notebook cell, so the file can be
# converted 1:1 into notebook cells (see `build_workflow_v1_7_3.py`, which is
# used to produce `Workflow-v1.7.3.ipynb` from this file plus
# `ES-011-A_19312_2-2_Q3_CD1_1.json`).
#
# Strategy change vs. the original section
# -----------------------------------------
# The original notebook picked the optimal Rabi (drive) length, integration
# length/delay, and readout amplitude/length by *minimizing* `rel_std_0`, the
# relative standard deviation of the ground-state shots projected onto the
# g/e discrimination axis. That metric only looks at two of the three
# prepared states (g, e) and only along a single axis.
#
# Here, every sweep instead evaluates the **g/e/f correct-state assignment
# fidelity** (the average of the diagonal of the 3x3 assignment/confusion
# matrix produced by the `iq_blobs` analysis workflow) at each sweep point,
# and picks the point with the *highest* fidelity. `rel_std_0` is still
# computed and plotted for reference/comparison, but it is no longer the
# quantity used to pick the optimum.
#
# For the two 2D sweeps (integration length & delay, readout amplitude &
# length) a heat map of the assignment fidelity is added, in addition to the
# existing line plots.

# %% [markdown]
# # Single Shot 0 and 1 Measurements <a class="anchor" id="single-shot-0-and-1-measurements"></a>

# %% [markdown]
# Single-shot (unaveraged) readout of the qubit prepared in g, e (and f).
#
# 1. **One Single Shot Measurement** — acquire the single shots for each prepared
#    state, classify them with a linear discriminant, and quantify the readout
#    with the state distance, the relative shot noise and the correct-state
#    assignment fidelity.
# 2. **Single Shot vs. Drive Pulse Length** — repeat the measurement for a range
#    of pi-pulse lengths (i.e. Rabi frequencies) and keep the length that
#    *maximizes* the g/e/f assignment fidelity.
# 3. **Single Shot vs. Integration Length and Delay** — repeat the measurement
#    for a range of integration delays and integration lengths at a fixed
#    readout pulse and keep the combination that *maximizes* the assignment
#    fidelity.
# 4. **Single Shot vs. Readout Amplitude and Length** — repeat the measurement
#    for a range of readout amplitudes and readout lengths and keep the
#    combination that *maximizes* the assignment fidelity.
#
# Sections 2-4 used to select the optimum from the *relative standard
# deviation of state 0* (`rel_std_0`), a proxy built only from the g/e shots
# projected onto the line connecting their means. This notebook instead uses,
# at every sweep point, the full **g/e/f correct-state assignment fidelity**
# returned by the `iq_blobs` analysis workflow, i.e. the average of the
# diagonal of the 3x3 assignment/confusion matrix, and picks the sweep point
# with the *highest* fidelity. `rel_std_0` is still computed and plotted for
# reference, but the optimum is no longer chosen from it.
#
# The readout parameters optimized in `# Readout Optimization` are the starting
# point here; the best settings found below are written back into the QPU.

# %% [markdown]
# ## One Single Shot Measurement

# %% [markdown]
# #### Experiment Parameters

# %%
update_global_parameters = True

states = 'gef'

n_avg_exponent = 17

# TODO
# readout settings for the single shots
# readout_length = 2e-6
readout_integration_length = 1.25e-6
# readout_amplitude = 0.2
# readout_integration_delay = 80e-9
# readout_range_out = -30
# readout_range_in = -40
# drive_range = -10
# use a long value only if you want to see the thermal population;
# 500e-3 makes 2**17 shots per state extremely slow
# reset_delay_length = 300e-6

# length and amplitude come from readout_length / readout_amplitude.
# readout_pulse = {
#     'function': 'const',
# }

qubit_to_measure = qubits[0]

temporary_parameters = {}
temp_pars = deepcopy(qubits[0].parameters)
# temp_pars.readout_amplitude = readout_amplitude
# temp_pars.readout_length = readout_length
# temp_pars.readout_pulse = readout_pulse
temp_pars.readout_integration_length = readout_integration_length
# temp_pars.readout_integration_delay = readout_integration_delay
# temp_pars.readout_range_out = readout_range_out
# temp_pars.readout_range_in = readout_range_in
# temp_pars.drive_range = drive_range
# temp_pars.reset_delay_length = reset_delay_length
temporary_parameters[qubit_to_measure.uid] = temp_pars

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
result = workflow_result.output
shots_per_state = collect_shots_from_result(result, qubit_to_measure.uid, states)

# convenience aliases matching the old variable names
zero_data = shots_per_state['g']
one_data = shots_per_state['e']
two_data = shots_per_state['f']

shots_arr = np.array([shots_per_state[s] for s in states])
print('Shots array shape (states, shots):', shots_arr.shape)

state_labels = {'g': 'ground', 'e': 'first excited', 'f': 'second excited'}
state_colors = {'g': 'b', 'e': 'r', 'f': 'y'}
state_alphas = {'g': 0.1, 'e': 0.1, 'f': 0.01}

# %%
states = 'gef'

# %%
# plot measurement data on IQ, plus the state means
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

# plt.xlim(-0.1, 0.12); plt.ylim(-0.25, 0.05) - set manually if needed
# ax.set_xlim(-0.1, 0.12)
# ax.set_ylim(-0.25, 0.05)

figname = 'Single_shot_points_'
file_path = get_path_to_file(figname, '.png')
fig.savefig(file_path, dpi=600, format='png', bbox_inches='tight')

# %%
# analize_Single_Shots(SS_results, plot=True)
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
# plot the raw (unrotated) distributions
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
# relative-distance histogram of the projected shots
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
# single Gaussian fit of the projected state-0 shots
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
# bimodal fit of the projected state-1 shots -> residual ground pop.
data = one_data_proj / r

fig, ax = plt.subplots()
y, x, patches = ax.hist(data, bins=n_bins, color='red', alpha=0.25)
x = (x[1:] + x[:-1]) / 2

expected = (-1, .2, y.max()*0.5, 1, .2, y.max()*0.5)
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
# bimodal fit of the projected state-0 shots -> residual excited pop.
data = zero_data_proj / r

fig, ax = plt.subplots()
y, x, patches = ax.hist(data, bins=n_bins, color='blue', alpha=0.25)
x = (x[1:] + x[:-1]) / 2

expected = (-1.5, 1.0, y.max()*0.5, 1, 1.0, y.max()*0.5)
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
# 2D histogram of the shots
n_bins = 50

fig, ax = plt.subplots(tight_layout=True)
ax.set_title(f'Single-shot density - {qubit_to_measure.uid}')
ax.hist2d(zero_data.real, zero_data.imag, n_bins)
ax.hist2d(one_data.real, one_data.imag, n_bins)
ax.set_xlabel('Real part, a.u.')
ax.set_ylabel('Imaginary part, a.u.')

# %%
# the assignment matrix produced by the iq_blobs analysis replaces the manual
# LinearDiscriminantAnalysis / compute_pca cells.
if qubit_to_measure.uid in assignment_matrices:
    print('Correct-state-assignment matrix:')
    print(np.round(assignment_matrices[qubit_to_measure.uid], 4))
    print('Assignment fidelity:', f'{assignment_fidelity * 100:0.2f} %')

# %% [markdown]
# #### Update Parameters

# %%
# Data_SS = {...}; Data_SS.update(qubit_parameters._params);
# savemat(get_path_to_file('Single_shots_all_unsh_', '.mat'), Data_SS)
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

# %%
qpu.quantum_elements

# %% [markdown]
# ## Single Shot Measurement for Different Rabi Frequencies
#
# *Optimum: the drive length / Rabi frequency with the highest g/e/f
# assignment fidelity (previously: the smallest Relative STD state 0).*

# %% [markdown]
# #### Experiment Parameters

# %%
update_global_parameters = False

n_avg_exponent = 15  # reduce: this is a sweep over 36 pi-pulse lengths

# NEW: sweep over all three states so that the g/e/f assignment fidelity
# (the new optimization criterion) is available at every drive length.
states = 'gef'

drive_length_arr = np.linspace(60e-9, 400e-9, 36)
rabi_freq_arr = 1 / drive_length_arr

# ge_drive_pulse = {
#     'function': 'gaussian',
#     'sigma': 0.25,
# }

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
    # temp_pars.ge_drive_pulse = ge_drive_pulse
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

    # diagnostic-only, g/e relative STD (kept for reference/comparison)
    res = analyze_single_shots(shots, state_0='g', state_1='e', plot=False)
    ss_drive_length_sweep_metrics.append(
        {k: v for k, v in res.items() if isinstance(v, (int, float, complex))}
    )
    # NEW: g/e/f assignment fidelity - the metric used to pick the optimum
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

# NEW: the optimum is the drive length with the *highest* g/e/f assignment
# fidelity (previously: the smallest relative STD of state 0).
optimal_index = int(np.nanargmax(fidelity_arr))
print('Best drive length:', round(drive_length_arr[optimal_index] * 1e9, 3), 'ns',
      '| Rabi frequency:', round(rabi_freq_arr[optimal_index] * 1e-6, 3), 'MHz',
      '| assignment fidelity:', f'{fidelity_arr[optimal_index] * 100:0.2f} %')

fig, ax = plt.subplots(2, 1, sharex=True, figsize=(10, 8))
fig.suptitle(f'Single shot vs. Rabi frequency - {qubit_to_measure.uid}', fontsize=16)
fig.supxlabel('Rabi frequency, MHz')

ax[0].plot(rabi_freq_arr * 1e-6, fidelity_arr * 100, '.k')
ax[0].set_ylabel('Assignment fidelity, %')

ax[1].plot(rabi_freq_arr * 1e-6, rel_std_0_arr, '.k')
ax[1].set_ylabel('Relative STD state 0')
ax[1].set_yscale('log')

for axis in ax:
    axis.axvline(x=rabi_freq_arr[optimal_index] * 1e-6, ls='-.', color='r',
                 label='optimal (max fidelity)')
    axis.legend()

file_path = get_path_to_file('Single_shots_vs_rabi_freq_', '.png')
fig.savefig(file_path, dpi=600, format='png', bbox_inches='tight')

# %% [markdown]
# #### Update Parameters

# %%
data_ss = {
    'ss_drive_length_sweep_arr': ss_drive_length_sweep_arr,
    'states': list(states),
    'ge_drive_length': drive_length_arr,
    'rabi_freq': rabi_freq_arr,
    'ge_drive_amplitude_pi': ge_drive_amplitude_pi_arr,
    'assignment_fidelity': fidelity_arr,
    'rel_std_0': rel_std_0_arr,
    'optimal_index': optimal_index,
    'n_shots': 2**n_avg_exponent,
    'comment': ('Sweep of the pi-pulse length, array dim [drive_length, state, shot]. '
                'Optimal point maximizes assignment_fidelity (g/e/f).'),
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
    # temp_pars.ge_drive_pulse = ge_drive_pulse
    qubit_to_measure.parameters = temp_pars
    save(qpu, qpu_file_path)
    print('Updated global experiment parameters!\n')

print('ge drive length: ', qubit_to_measure.parameters.ge_drive_length)
print('ge drive amplitude pi: ', qubit_to_measure.parameters.ge_drive_amplitude_pi)

# %%
float(drive_length_arr[optimal_index])

# %%
float(ge_drive_amplitude_pi_arr[optimal_index])

# %%
qpu.quantum_elements

# %% [markdown]
# ## Single Shot Measurement for Different Integration Lengths and Delays
#
# *Optimum: the (integration length, integration delay) combination with the
# highest g/e/f assignment fidelity (previously: the smallest Relative STD
# state 0).*

# %% [markdown]
# #### Experiment Parameters

# %%
update_global_parameters = True

n_avg_exponent = 16

# NEW: sweep over all three states so that the g/e/f assignment fidelity
# (the new optimization criterion) is available at every (delay, length).
states = 'gef'

qubit_to_measure = qubits[0]

print('Readout pulse length:', 
      qubit_to_measure.parameters.readout_length)

# TODO
# Here the readout pulse amplitude and length are fixed and we vary the
# integration delay and integration (weighting) length. The optimum is the
# combination with the highest g/e/f assignment fidelity.
readout_integration_delay_arr = np.linspace(60, 200, 2) * 1e-9
readout_integration_length_arr = np.linspace(1, 2, 3) * 1e-6

print('Readout integration delays (ns): ',
      readout_integration_delay_arr * 1e9)
print('Readout integration lengths (us):',
      readout_integration_length_arr * 1e6)

# %% [markdown]
# #### Run Workflow

# %%
options = iq_blobs.experiment_workflow.options()
options.count(2**n_avg_exponent)
options.close_figures(True)
# NEW: the analysis must run so that the g/e/f assignment fidelity - the new
# figure of merit for this sweep - is available at every point.
options.do_analysis(True)

ss_delay_sweep_shots = []
ss_delay_sweep_metrics = []
ss_delay_sweep_fidelities = []
ss_delay_sweep_matrices = []

for integration_delay in readout_integration_delay_arr:
    print('Integration delay:', round(integration_delay * 1e9, 3), 'ns')

    shots_inner = []
    metrics_inner = []
    fidelities_inner = []
    matrices_inner = []

    for integration_length in readout_integration_length_arr:
        print('  Integration length:', round(integration_length * 1e6, 3), 'us')

        temporary_parameters = {}
        temp_pars = deepcopy(qubit_to_measure.parameters)
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

        # diagnostic-only, g/e relative STD (kept for reference/comparison)
        res = analyze_single_shots(shots, state_0='g', state_1='e', plot=False)
        metrics_inner.append(
            {k: v for k, v in res.items() if isinstance(v, (int, float, complex))}
        )

        # NEW: g/e/f assignment fidelity - the metric used to pick the optimum
        fidelities_inner.append(
            workflow_result.tasks['analysis_workflow'].output.get(
                qubit_to_measure.uid, np.nan
            )
        )
        matrices_inner.append(
            get_analysis_task_output(
                workflow_result, 'calculate_assignment_matrices'
            ).get(qubit_to_measure.uid)
        )

    ss_delay_sweep_shots.append(shots_inner)
    ss_delay_sweep_metrics.append(metrics_inner)
    ss_delay_sweep_fidelities.append(fidelities_inner)
    ss_delay_sweep_matrices.append(matrices_inner)

ss_delay_sweep_arr = np.array(ss_delay_sweep_shots)
print('Sweep array shape (delays, integration lengths, states, shots):',
      ss_delay_sweep_arr.shape)

# %% [markdown]
# #### Analysis Plots

# %%
# NEW: pick the (delay, integration length) combination with the highest
# g/e/f assignment fidelity, instead of the smallest Relative STD state 0.
# fidelity_arr has shape [delay, integration_length].
fidelity_arr = np.array(ss_delay_sweep_fidelities, dtype=float)

flat_index = int(np.nanargmax(fidelity_arr))
optimal_delay_index, optimal_length_index = np.unravel_index(
    flat_index, fidelity_arr.shape
)
optimal_delay_index = int(optimal_delay_index)
optimal_length_index = int(optimal_length_index)

readout_integration_delay_opt = float(
    readout_integration_delay_arr[optimal_delay_index]
)
readout_integration_length_opt = float(
    readout_integration_length_arr[optimal_length_index]
)

print('Readout length is', readout_length)
print('Best assignment fidelity is',
      f'{fidelity_arr[optimal_delay_index, optimal_length_index] * 100:0.2f} %',
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
    ax.plot(readout_integration_delay_arr * 1e9, fidelity_arr[:, k] * 100, '.-',
            label=f'{integration_length * 1e9:.0f} ns')
ax.axvline(x=readout_integration_delay_opt * 1e9, ls='-.', color='r',
           label='optimal (max fidelity)')
ax.set_xlabel('Readout integration delay, ns')
ax.set_ylabel('Assignment fidelity, %')
ax.legend(title='Integration length')

file_path = get_path_to_file('Single_shots_vs_delay_and_int_len_', '.png')
fig.savefig(file_path, dpi=600, format='png', bbox_inches='tight')

# %%
# NEW: heat map of the g/e/f assignment fidelity.
# vertical axis = integration length, horizontal axis = integration delay.
fig, ax = plt.subplots(figsize=(10, 5))
ax.set_title(f'Assignment fidelity - {qubit_to_measure.uid}')
im = ax.pcolormesh(readout_integration_delay_arr * 1e9,
                   readout_integration_length_arr * 1e6,
                   fidelity_arr.T * 100, shading='nearest')
cb = fig.colorbar(im)
cb.set_label('Assignment fidelity, %')
ax.plot(readout_integration_delay_opt * 1e9, readout_integration_length_opt * 1e6,
        'rx', ms=12, label='optimal')
ax.set_xlabel('Readout integration delay, ns')
ax.set_ylabel('Readout integration length, us')
ax.legend()

file_path = get_path_to_file('Single_shots_delay_and_int_len_map_', '.png')
fig.savefig(file_path, dpi=600, format='png', bbox_inches='tight')

# %% [markdown]
# #### Update Parameters

# %%
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
data_ss = {
    'ss_delay_sweep_arr': ss_delay_sweep_arr,
    'states': list(states),
    'readout_integration_delay_sweep': readout_integration_delay_arr,
    'readout_integration_length_sweep': readout_integration_length_arr,
    'readout_length': readout_length,
    'assignment_fidelity': fidelity_arr,
    'rel_std_0': rel_std_0_arr,
    'optimal_delay_index': optimal_delay_index,
    'optimal_length_index': optimal_length_index,
    'n_shots': 2**n_avg_exponent,
    'comment': ('Sweep integration delay and integration length, array dim '
                '[delay, integration_length{, state, shot for ss_delay_sweep_arr}]. '
                'Optimal point maximizes assignment_fidelity (g/e/f).'),
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

best_matrix = ss_delay_sweep_matrices[optimal_delay_index][optimal_length_index]
if best_matrix is not None:
    print('Correct-state-assignment matrix at the optimal point:')
    print(np.round(best_matrix, 4))

# %%
qpu.quantum_elements

# %% [markdown]
# ## Single Shot Measurement for Different Readout Amplitudes and Lengths
#
# *Optimum: the (readout amplitude, readout length) combination with the
# highest g/e/f assignment fidelity (previously: the smallest Relative STD
# state 0).*

# %% [markdown]
# #### Experiment Parameters

# %%
update_global_parameters = False

n_avg_exponent = 16

# NEW: sweep over all three states so that the g/e/f assignment fidelity
# (the new optimization criterion) is available at every (amplitude, length).
states = 'gef'

# TODO
# Sweep power and length of the readout pulse. The integration delay is fixed
# and the integration window is equal to the readout pulse length. The
# optimum is the combination with the highest g/e/f assignment fidelity.
readout_amplitude_arr = np.linspace(0.05, 1, 20)
readout_length_arr = np.linspace(1900, 2000, 11) * 1e-9

readout_integration_delay = qubit_to_measure.parameters.readout_integration_delay

qubit_to_measure = qubits[0]

# %% [markdown]
# #### Run Workflow

# %%
options = iq_blobs.experiment_workflow.options()
options.count(2**n_avg_exponent)
options.close_figures(True)
# NEW: the analysis must run so that the g/e/f assignment fidelity - the new
# figure of merit for this sweep - is available at every point.
options.do_analysis(True)

ss_ro_sweep_metrics = []
ss_ro_sweep_fidelities = []
ss_ro_sweep_matrices = []

for readout_amplitude in readout_amplitude_arr:
    print('Readout amplitude:', round(float(readout_amplitude), 5))

    metrics_inner = []
    fidelities_inner = []
    matrices_inner = []

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
        # diagnostic-only, g/e relative STD (kept for reference/comparison)
        res = analyze_single_shots(shots, state_0='g', state_1='e', plot=False)
        metrics_inner.append(
            {k: v for k, v in res.items() if isinstance(v, (int, float, complex))}
        )

        # NEW: g/e/f assignment fidelity - the metric used to pick the optimum
        fidelities_inner.append(
            workflow_result.tasks['analysis_workflow'].output.get(
                qubit_to_measure.uid, np.nan
            )
        )
        matrices_inner.append(
            get_analysis_task_output(
                workflow_result, 'calculate_assignment_matrices'
            ).get(qubit_to_measure.uid)
        )

    ss_ro_sweep_metrics.append(metrics_inner)
    ss_ro_sweep_fidelities.append(fidelities_inner)
    ss_ro_sweep_matrices.append(matrices_inner)

# %% [markdown]
# #### Analysis Plots

# %%
# NEW: pick the (amplitude, length) combination with the highest g/e/f
# assignment fidelity, instead of the smallest Relative STD state 0.
# fidelity_arr has shape [readout_amplitude, readout_length].
fidelity_arr = np.array(ss_ro_sweep_fidelities, dtype=float)
rel_std_0_arr = np.array(
    [[m['rel_std_0'] for m in metrics_inner] for metrics_inner in ss_ro_sweep_metrics]
)

flat_index = int(np.nanargmax(fidelity_arr))
optimal_amp_index, optimal_len_index = np.unravel_index(
    flat_index, fidelity_arr.shape
)
optimal_amp_index = int(optimal_amp_index)
optimal_len_index = int(optimal_len_index)

readout_amplitude_opt = float(readout_amplitude_arr[optimal_amp_index])
readout_length_opt = float(readout_length_arr[optimal_len_index])

print('Best assignment fidelity is',
      f'{fidelity_arr[optimal_amp_index, optimal_len_index] * 100:0.2f} %',
      'for amplitude', np.round(readout_amplitude_opt, 3),
      '(index', optimal_amp_index, ') and length', readout_length_opt,
      '(index', optimal_len_index, ').')

fig, ax = plt.subplots(figsize=(10, 5))
ax.set_title(f'Single shot vs. readout amplitude - {qubit_to_measure.uid}')
for k, readout_length in enumerate(readout_length_arr):
    ax.plot(readout_amplitude_arr, fidelity_arr[:, k] * 100, '.-',
            label=f'{readout_length * 1e9:.0f} ns')
ax.axvline(x=readout_amplitude_opt, ls='-.', color='r', label='optimal (max fidelity)')
ax.set_xlabel('Readout amplitude, a.u.')
ax.set_ylabel('Assignment fidelity, %')
ax.legend(title='Readout length', ncol=2)

file_path = get_path_to_file('Single_shots_vs_ro_amp_and_ro_len_', '.png')
fig.savefig(file_path, dpi=600, format='png', bbox_inches='tight')

# %%
# NEW: heat map of the g/e/f assignment fidelity.
# vertical axis = readout amplitude, horizontal axis = readout length.
fig, ax = plt.subplots(figsize=(10, 5))
ax.set_title(f'Assignment fidelity - {qubit_to_measure.uid}')
im = ax.pcolormesh(readout_length_arr * 1e9, readout_amplitude_arr,
                   fidelity_arr * 100, shading='nearest')
cb = fig.colorbar(im)
cb.set_label('Assignment fidelity, %')
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
    'assignment_fidelity': fidelity_arr,
    'rel_std_0': rel_std_0_arr,
    'optimal_amp_index': optimal_amp_index,
    'optimal_len_index': optimal_len_index,
    'n_shots': 2**n_avg_exponent,
    'comment': ('Sweep readout amplitude and readout length, array dim '
                '[readout_amplitude, readout_length]. Optimal point maximizes '
                'assignment_fidelity (g/e/f).'),
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

best_matrix = ss_ro_sweep_matrices[optimal_amp_index][optimal_len_index]
if best_matrix is not None:
    print('Correct-state-assignment matrix at the optimal point:')
    print(np.round(best_matrix, 4))

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
