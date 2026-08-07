"""Readout Optimization — cell-by-cell code for ES-008-BC_2-1_8853_CD2.

Port of the "Readout optimization" section of `S3_Q2_Cooldown_2.json`
(old, hand-rolled LabOne Q DSL) to the LabOneQ *workflow* architecture and the
layout used by `ES-008-BC_2-1_8853_CD2_duplicate.json`
(`## Section` -> `#### Experiment Parameters` / `#### Run Workflow` /
`#### Update Parameters`).

Cells are delimited with jupytext markers:
    `# %% [markdown]`  -> markdown cell
    `# %%`             -> code cell
Copy each block into its own notebook cell, replacing cell 77
(`#TODO: Implement readout optimization ...`) under the existing
`# Readout Optimization` heading (cell 76).

-------------------------------------------------------------------------------
OLD -> NEW PARAMETER / API NAME MAPPING
-------------------------------------------------------------------------------
Qubit parameters (old `qubit_parameters[...]` / `lo_settings[...]`
-> new `qubits[0].parameters.<attr>` == `TunableTransmonQubitParameters`):

    qubit_parameters["ro_amp"]        -> readout_amplitude
    qubit_parameters["ro_len"]        -> readout_length
    readout_weighting_function.length -> readout_integration_length
    readout_weighting_function (const)-> readout_integration_kernels_type = "default"
                                        (const kernel of readout_integration_length)
    qubit_parameters["ro_int_delay"]  -> readout_integration_delay
    qubit_parameters["ro_freq"]       -> readout_resonator_frequency  (ABSOLUTE now:
                                        old ro_freq was an IF, absolute freq was
                                        lo_settings["ro_lo"] + ro_freq)
    qubit_parameters["ro_freq_opt"]   -> readout_resonator_frequency (optimal value)
    lo_settings["ro_lo"]              -> readout_lo_frequency
    qubit_parameters["relax"]         -> reset_delay_length
    readout_opt["readout_range"] /
        lsg_q0["measure_line"].range  -> readout_range_out  (input: readout_range_in)
    pulse_library.gaussian_square(
        uid=..., length=ro_len,
        amplitude=ro_amp,
        width=ro_len*0.95)            -> readout_pulse = {"function": "gaussian_square",
                                                          "width": readout_length*0.95}
                                        (length/amplitude come from readout_length /
                                         readout_amplitude, so they are NOT repeated
                                         in the pulse dict)
    x180 / x180_ef                    -> qops.x180(q, transition=...) via
                                        `qop.prepare_state(q, "e"/"f")` inside the
                                        dispersive-shift workflow
    n_average (= exponent)            -> n_avg_exponent, used as
                                        options.count(2**n_avg_exponent)
    ro_amp_min/ro_amp_max/
        ro_amp_points/ro_amp_arr      -> ro_amp_min/ro_amp_max/n_ro_amp/ro_amp_arr
    spec_range / spec_num             -> freq_range / n_points
    readout_opt (QBaseParameters)     -> temporary_parameters[q.uid]
                                        (a deepcopy'd TunableTransmonQubitParameters)
    qsample_params / sample_parameters-> sample_name, qubit_name,
                                        cooldown_start_date, data_root_directory

Experiment/API level:

    make_rabi(...) + my_session.compile/run
                                      -> amplitude_rabi.experiment_workflow(...).run()
    create_res_spec_gef(level=0/1/2)  -> dispersive_shift.experiment_workflow(
                                            ..., states="gef")
    fit_Rabi -> popt/pcov             -> analysis_workflow task "fit_data" -> lmfit
                                        ModelResult; popt == params[p].value,
                                        sqrt(diag(pcov)) == params[p].stderr for
                                        p in ("frequency", "phase", "amplitude",
                                        "offset")  (same order as the old popt)
    argmax(|res_0 - res_1|)           -> dispersive-shift analysis
                                        `calculate_signal_differences` /
                                        `extract_qubit_parameters`
    exp.set_signal_map(qubit_meas_map)-> handled by qpu / qubit.signals
    get_path_to_file(...) + savemat   -> folder_store (automatic) + optional
                                        legacy .mat export via get_path_to_file()
    qubit_parameters.update_parameter -> temp_pars.<attr> = ... then
                                        `qubit_to_measure.parameters = deepcopy(...)`
                                        and `<experiment>.update_qpu(qpu, ...)`

REQUIRED IMPORT CHANGE (notebook cell 5, LabOne Q Libraries):
add `dispersive_shift` to the `from laboneq_applications.experiments import (...)`
list.
-------------------------------------------------------------------------------
"""

# %% [markdown]
# # Readout Optimization
#
# Optimization of the readout pulse amplitude and of the readout (resonator)
# frequency.
#
# 1. **Readout Amplitude Optimization** — sweep the readout amplitude and run an
#    amplitude-Rabi experiment at each amplitude. The readout amplitude with the
#    smallest relative Rabi-fit errors gives the best signal-to-noise ratio.
# 2. **Dispersive Shift** — resonator spectroscopy with the qubit prepared in
#    g, e (and f). The optimal readout frequency is the frequency of the largest
#    distance between the transmission signals of the different states.
# 3. **Readout Settings Summary** — write the optimized readout parameters into
#    the QPU and save them.

# %% [markdown]
# ## Helpers

# %%
# Helpers used by the readout-optimization cells.
# Replaces the old `get_path_to_file(figname, '.png', sample_parameters)` and the
# manual `popt`/`pcov` bookkeeping of the old notebook.
import attrs
import matplotlib.pyplot as plt
from scipy.io import savemat
from laboneq.simple import dsl

from laboneq_applications.experiments import dispersive_shift  # add to cell 5 imports


def get_path_to_file(file_name: str, extension: str, directory: str | None = None) -> str:
    """Timestamped file path inside the cooldown data directory.

    New-structure replacement for the old
    `get_path_to_file(figname, '.png', sample_parameters)`.
    """
    directory = data_root_directory if directory is None else directory
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    return os.path.join(directory, f'{timestamp}_{file_name}{extension}')


def get_analysis_task_output(workflow_result, task_name: str):
    """Output of a task inside the nested `analysis_workflow` of a workflow result.

    Used to reach the raw lmfit results (`fit_data`) and the pair-wise signal
    distances (`calculate_signal_differences`), which are not part of the
    analysis-workflow output itself.
    """
    return workflow_result.tasks['analysis_workflow'].tasks[task_name].output


# %% [markdown]
# ## Readout Amplitude Optimization

# %% [markdown]
# #### Experiment Parameters

# %%
update_global_parameters = True

transition = set_transition('ge')

n_avg_exponent = 12  # old: n_average = 12

# Readout settings used during the sweep.
# old: lsg_q0["measure_line"].range = -20, pulse_length = 2e-6,
#      qubit_parameters["ro_len"], qubit_parameters["ro_int_delay"],
#      qubit_parameters["relax"]
readout_range_out = -20
readout_range_in = -45
readout_length = 2e-6
readout_integration_length = 2e-6
readout_integration_delay = 80e-9
reset_delay_length = 150e-6

# old: pulse_library.gaussian_square(uid="readout_pulse", length=ro_len,
#                                   amplitude=ro_amp, width=ro_len*0.95)
# length and amplitude are taken from readout_length / readout_amplitude.
readout_pulse = {
    'function': 'gaussian_square',
    'width': readout_length * 0.95,
}

# Readout amplitude sweep. old: ro_amp_min / ro_amp_max / ro_amp_points -> ro_amp_arr
ro_amp_min = 0.0
ro_amp_max = 1.0
n_ro_amp = 11
ro_amp_arr = np.linspace(ro_amp_min, ro_amp_max, n_ro_amp)

# Rabi sweep used to benchmark each readout amplitude (old: `rabi_sweep`).
drive_range = -5
amp_min = 0
amp_max = 1
n_amp = 21
drive_amplitudes = np.linspace(amp_min, amp_max, n_amp)

qubit_to_measure = qubits[0]

# %% [markdown]
# #### Run Workflow

# %%
# old: for ro_amp in ro_amp_arr: make_rabi(...) -> my_session.compile/run -> fit_Rabi
options = amplitude_rabi.experiment_workflow.options()
options.count(2**n_avg_exponent)
options.update(False)  # never update the qubit parameters during the sweep
options.close_figures(True)  # one Rabi figure per readout amplitude

options.transition(transition)
options.cal_states(transition)

qubits_to_measure = [qubit_to_measure]

# old: rabi_sw_res / popt_rabi_sw / pcov_rabi_sw
rabi_ro_sweep_results = []
fit_values_ro_sweep = []
fit_errors_ro_sweep = []
# same order as the old popt/pcov of fit_Rabi
fit_parameter_names = ['frequency', 'phase', 'amplitude', 'offset']

for ro_amp in ro_amp_arr:
    print('Measure at readout amplitude:', round(ro_amp, 5))

    temporary_parameters = {}
    temp_pars = deepcopy(qubits[0].parameters)
    temp_pars.readout_amplitude = round(ro_amp, 5)
    temp_pars.readout_length = readout_length
    temp_pars.readout_pulse = readout_pulse
    temp_pars.readout_integration_length = readout_integration_length
    temp_pars.readout_integration_delay = readout_integration_delay
    temp_pars.readout_range_out = readout_range_out
    temp_pars.readout_range_in = readout_range_in
    temp_pars.reset_delay_length = reset_delay_length
    temp_pars.drive_range = drive_range
    temporary_parameters[qubit_to_measure.uid] = temp_pars

    exp_workflow = amplitude_rabi.experiment_workflow(
        session=session,
        qpu=qpu,
        qubits=[q.uid for q in qubits_to_measure],
        amplitudes=[drive_amplitudes for q in qubits_to_measure],
        options=options,
        temporary_parameters=temporary_parameters,
    )
    workflow_result = exp_workflow.run()
    rabi_ro_sweep_results.append(workflow_result)

    # old: popt_norm, pcov_norm = fit_Rabi(...); the workflow analysis already
    # rotates/projects the raw data and fits a cosine model to the population.
    fit_results = get_analysis_task_output(workflow_result, 'fit_data')
    fit_res = fit_results.get(qubit_to_measure.uid)
    if fit_res is None:
        print(f'  Rabi fit failed at readout amplitude {round(ro_amp, 5)}.')
        fit_values_ro_sweep.append([np.nan] * len(fit_parameter_names))
        fit_errors_ro_sweep.append([np.nan] * len(fit_parameter_names))
        continue

    fit_values_ro_sweep.append([fit_res.params[p].value for p in fit_parameter_names])
    fit_errors_ro_sweep.append([fit_res.params[p].stderr for p in fit_parameter_names])

# old: popt_rabi_arr / err_arr
popt_rabi_arr = np.array(fit_values_ro_sweep, dtype=float)
err_arr = np.array(fit_errors_ro_sweep, dtype=float)

# %% [markdown]
# #### Update Parameters

# %%
# old: relative-error plot of the Rabi fit parameters vs readout amplitude
# (freq / phase / amp / off) + 'Rabi_optimiz_20dBm_' figure.
ll = 1  # skip readout amplitude 0 (no signal)
ul = None  # old: ul = -1
sweep_slice = slice(ll, ul)

# lmfit reports stderr = 0 when the covariance matrix could not be estimated;
# treat those points as invalid instead of "perfect".
err_arr[err_arr == 0] = np.nan
rel_err_arr = np.abs(err_arr / popt_rabi_arr)

fig, ax = plt.subplots(2, 2, sharex=True, figsize=(10, 8))
fig.suptitle(f'Relative errors for Rabi measurements - {qubit_to_measure.uid}', fontsize=16)
fig.supxlabel('Readout amplitude (a.u.)')
fig.supylabel('Relative error (a.u.)')

ax[0, 0].plot(ro_amp_arr[sweep_slice], rel_err_arr[sweep_slice, 0], '.k', label='freq')
ax[1, 0].plot(ro_amp_arr[sweep_slice], rel_err_arr[sweep_slice, 1], '.k', label='phase')
ax[0, 1].plot(ro_amp_arr[sweep_slice], rel_err_arr[sweep_slice, 2], '.k', label='amp')
ax[1, 1].plot(ro_amp_arr[sweep_slice], rel_err_arr[sweep_slice, 3], '.k', label='off')

ax[0, 0].set_title('Frequency')
ax[1, 0].set_title('Phase')
ax[0, 1].set_title('Amplitude')
ax[1, 1].set_title('Offset')

# Optimal readout amplitude: smallest mean relative fit error.
mean_rel_err = np.nanmean(rel_err_arr, axis=1)
masked_rel_err = np.full(mean_rel_err.shape, np.nan)
masked_rel_err[sweep_slice] = mean_rel_err[sweep_slice]
optimal_index = int(np.nanargmin(masked_rel_err))
readout_amplitude_opt = float(ro_amp_arr[optimal_index])

for axis in ax.flatten():
    axis.axvline(x=readout_amplitude_opt, ls='-.', color='r', label='optimal')
    axis.legend()

print('Optimal readout amplitude:', round(readout_amplitude_opt, 5))

# old: figname = 'Rabi_optimiz_20dBm_'; get_path_to_file(figname, '.png', sample_parameters)
figname = f'Rabi_optimiz_{readout_range_out}dBm_'
file_path = get_path_to_file(figname, '.png')
fig.savefig(file_path, dpi=600, format='png', bbox_inches='tight')

# %%
# old: qubit_parameters.update_parameter("ro_amp", 0.5)
#      qubit_parameters.update_parameter("ro_len", 2e-6)
# Set to a value != None to override the value extracted above.
manual_readout_amplitude = None
if manual_readout_amplitude is not None:
    readout_amplitude_opt = float(manual_readout_amplitude)

if update_global_parameters:
    temporary_parameters[qubit_to_measure.uid].readout_amplitude = readout_amplitude_opt
    qubit_to_measure.parameters = deepcopy(temporary_parameters[qubit_to_measure.uid])
    save(qpu, qpu_file_path)
    print('Updated global experiment parameters!\n')

# old: print('Readout length/amplitude/Wfunc length: ', ...)
print('Readout amplitude: ', qubit_to_measure.parameters.readout_amplitude)
print('Readout length: ', qubit_to_measure.parameters.readout_length)
print('Readout pulse: ', qubit_to_measure.parameters.readout_pulse)
print('Readout integration length: ', qubit_to_measure.parameters.readout_integration_length)
print('Readout integration delay: ', qubit_to_measure.parameters.readout_integration_delay)
print('Readout range out / in: ', qubit_to_measure.parameters.readout_range_out,
      '/', qubit_to_measure.parameters.readout_range_in)

# %% [markdown]
# ## Dispersive Shift
#
# Resonator spectroscopy with the qubit prepared in different states
# (old: *Spectroscopy of resonator in different states*, `create_res_spec_gef`
# with `level = 0, 1, 2`). Use `states = 'ge'` if the e-f transition is not
# calibrated yet.

# %% [markdown]
# #### Experiment Parameters

# %%
update_global_parameters = True

states = 'gef'  # old: level = 0 / 1 / 2 -> 'g' / 'e' / 'f'

n_avg_exponent = 12  # old: n_average = 12

freq_range = 2e6  # old: spec_range
n_points = 101  # old: spec_num

# old: `readout_low` readout definition used for the gef spectroscopy
readout_amplitude = 0.2
readout_range_out = -25
readout_range_in = -45
reset_delay_length = 120e-6  # old: qubit_parameters.update_parameter("relax", 120e-6)

temporary_parameters = {}
temp_pars = deepcopy(qubits[0].parameters)
temp_pars.readout_amplitude = readout_amplitude
temp_pars.readout_range_out = readout_range_out
temp_pars.readout_range_in = readout_range_in
temp_pars.reset_delay_length = reset_delay_length
temporary_parameters[qubits[0].uid] = temp_pars

# %% [markdown]
# #### Run Workflow

# %%
# old: exp_spec_g/e/f = create_res_spec_gef(freq_sweep_ST, x180, x180_ef, readout_low,
#                                          n_average, level=0/1/2)
#      -> three compiles + three runs. The dispersive-shift workflow does all
#         states in a single experiment and analyses them together.
options = dispersive_shift.experiment_workflow.options()
options.count(2**n_avg_exponent)
options.update(False)  # updated explicitly below
options.close_figures(False)

qubit_to_measure = qubits[0]

# old: freq_sweep_ST = LinearSweepParameter(start=ro_freq - spec_range/2,
#                                          stop=ro_freq + spec_range/2, count=spec_num)
# Frequencies are absolute now (no lo_settings["ro_lo"] offset needed).
frequencies = temporary_parameters[
    qubit_to_measure.uid
].readout_resonator_frequency + np.linspace(-freq_range / 2, freq_range / 2, n_points)

exp_workflow = dispersive_shift.experiment_workflow(
    session=session,
    qpu=qpu,
    qubit=qubit_to_measure.uid,
    frequencies=frequencies,
    states=states,
    options=options,
    temporary_parameters=temporary_parameters,
)
workflow_result = exp_workflow.run()

# %% [markdown]
# #### Analysis Plots

# %%
# old: res_0_res / res_1_res / res_2_res + res_0_freq / res_1_freq / res_2_freq
# via spec_g_res.get_data("q0_res_spec_e") and .get_axis(...)[0] + ro_lo offset.
result = workflow_result.output
res_data = {
    state: result[dsl.handles.result_handle(qubit_to_measure.uid, suffix=state)].data
    for state in states
}
res_freq = frequencies

state_labels = {'g': 'ground', 'e': 'first excited', 'f': 'second excited'}
state_colors = {'g': 'b', 'e': 'r', 'f': 'g'}

# old: amplitude/phase figure 'Readout_spec_for_g_e'
fig, ax = plt.subplots(2, 1, sharex=True, figsize=(10, 8))
fig.suptitle('Spectroscopy of readout resonator for the qubit states', fontsize=16)
fig.supxlabel('Readout frequency, GHz')

ax[0].set_title('Amplitude')
ax[1].set_title('Phase')

for state, data in res_data.items():
    ax[0].plot(res_freq * 1e-9, np.abs(data), state_colors[state], label=state_labels[state])
    ax[1].plot(res_freq * 1e-9, np.unwrap(np.angle(data)), state_colors[state],
               label=state_labels[state])

for axis, ylabel in zip(ax, ['Amplitude, a.u.', 'Phase, a.u.']):
    axis.axvline(x=qubit_to_measure.parameters.readout_resonator_frequency * 1e-9,
                 label='current readout')
    axis.set_ylabel(ylabel)
    axis.legend()

file_path = get_path_to_file('Readout_spec_for_g_e', '.png')
fig.savefig(file_path, dpi=600, format='png', bbox_inches='tight')

# old: IQ plot of the three states
fig_iq, ax_iq = plt.subplots()
ax_iq.set_title('Spectroscopy of readout resonator: IQ plane')
for state, data in res_data.items():
    ax_iq.plot(data.real, data.imag, state_colors[state], label=state_labels[state])
ax_iq.set_xlabel('Real part, a.u.')
ax_iq.set_ylabel('Imaginary part, a.u.')
ax_iq.legend()

file_path = get_path_to_file('Readout_spec_for_g_e_IQ', '.png')
fig_iq.savefig(file_path, dpi=600, format='png', bbox_inches='tight')

# %%
# old: distance plot np.abs(res_0_res - res_1_res) etc. + argmax -> optimal frequency.
# The analysis task `calculate_signal_differences` returns, per state pair
# (and 'sum' when more than two states are measured):
#   (distance_array, max_distance, frequency_at_max_distance)
processed_data_dict = get_analysis_task_output(workflow_result, 'calculate_signal_differences')

fig_dist, ax_dist = plt.subplots(figsize=(10, 5))
ax_dist.set_title('Spectroscopy of readout resonator: state distances')
for state_pair, (distance, max_distance, freq_at_max) in processed_data_dict.items():
    ax_dist.plot(res_freq * 1e-9, distance, label=state_pair)
    print(f'{state_pair}: max distance {max_distance:.4g} at '
          f'{freq_at_max * 1e-9:.6f} GHz')

ax_dist.axvline(x=qubit_to_measure.parameters.readout_resonator_frequency * 1e-9,
                ls='--', label='current readout')
ax_dist.axvline(x=processed_data_dict['sum' if 'sum' in processed_data_dict else
                                      next(iter(processed_data_dict))][2] * 1e-9,
                ls='-.', color='k', label='optimal')
ax_dist.set_xlabel('Readout frequency, GHz')
ax_dist.set_ylabel('Signal distance, a.u.')
ax_dist.legend()

file_path = get_path_to_file('Readout_spec_for_g_e_distance', '.png')
fig_dist.savefig(file_path, dpi=600, format='png', bbox_inches='tight')

# %% [markdown]
# #### Update Parameters

# %%
# old: qubit_parameters.update_parameter("ro_freq_opt",
#          res_1_freq[max_dist_arg] - lo_settings["ro_lo"])
analysis_workflow_result = workflow_result.tasks['analysis_workflow']
qubit_parameters = analysis_workflow_result.output
pprint(qubit_parameters)

readout_resonator_frequency_opt = float(
    qubit_parameters['new_parameter_values'][qubit_to_measure.uid][
        'readout_resonator_frequency'
    ]
)

# old: commented-out manual override
#      qubit_parameters.update_parameter("ro_freq_opt", 6.893e9 - lo_settings["ro_lo"])
manual_readout_resonator_frequency = None
if manual_readout_resonator_frequency is not None:
    readout_resonator_frequency_opt = float(manual_readout_resonator_frequency)
    qubit_parameters['new_parameter_values'][qubit_to_measure.uid][
        'readout_resonator_frequency'
    ] = readout_resonator_frequency_opt

print(f'ro freq opt: {readout_resonator_frequency_opt * 1e-9:.6f} GHz')

if update_global_parameters:
    temporary_parameters[qubit_to_measure.uid].readout_resonator_frequency = (
        readout_resonator_frequency_opt
    )
    qubit_to_measure.parameters = deepcopy(temporary_parameters[qubit_to_measure.uid])
    dispersive_shift.update_qpu(qpu, qubit_parameters['new_parameter_values'])
    save(qpu, qpu_file_path)
    print('Updated global experiment parameters!\n')

print('Readout resonator frequency: ',
      qubit_to_measure.parameters.readout_resonator_frequency * 1e-9, ' GHz')

# %%
# old: Data_gef_spec = {...}; Data_gef_spec.update(qubit_parameters._params);
#      savemat(get_path_to_file('ge_spec_readout_test_', '.mat', sample_parameters), ...)
# The FolderStore already saves the workflow results; this is the legacy .mat export.
data_gef_spec = {'freq': res_freq}
for state, data in res_data.items():
    data_gef_spec[f'{state}_res'] = data
    data_gef_spec[f'{state}_freq'] = res_freq
data_gef_spec.update(
    {k: v for k, v in attrs.asdict(qubit_to_measure.parameters).items()
     if isinstance(v, (int, float, str))}
)
data_gef_spec['sample_name'] = sample_name
data_gef_spec['qubit_name'] = qubit_name
data_gef_spec['cooldown_start_date'] = cooldown_start_date

file_path = get_path_to_file('ge_spec_readout_', '.mat')
savemat(file_path, data_gef_spec)
print(f'Saved gef readout spectroscopy to: {file_path}')

# %% [markdown]
# ## Readout Settings Summary

# %%
# old: readout_opt = {'readout_type': 'pulse', 'readout_pulse': readout_pulse,
#                     'readout_weighting_function': readout_weighting_function,
#                     'relax_time': ..., 'measure_freq': ..., 'acquire_freq': ...,
#                     'readout_range': -20, 'readout_delay': ...}
#           -> QBaseParameters(...)
# New structure: the optimized readout lives directly in the qubit parameters,
# so the readout_opt dict is only a readable summary.
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
qubits[0]
