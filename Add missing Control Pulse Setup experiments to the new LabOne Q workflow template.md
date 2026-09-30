# Problem statement
The old notebook `ES-008-BC_2-1_8853_Q3_Cooldown2.json` has a "Control Pulse Setup" section built with raw, manual LabOne Q code (dict-based `qubit_parameters`/`lo_settings`, hand-built `Experiment` objects, `my_session.compile/run`). The new template `ES-Workflow_template.json` has an equivalent "Control Pulses" section already, but built entirely on the LabOne Q **Applications Library** workflow API (`qubits[i].parameters.*`, `qpu`, `session`, `*.experiment_workflow(...).run()`). Some experiments from the old notebook were never ported to the new workflow style. The user wants those missing experiments implemented in the new style and dropped into a standalone `workflows/control_pulse_setup.py` (cell-by-cell, Jupytext `# %%` format) for manual insertion into the notebook later — not directly into any `.json`/`.ipynb` file.


# Current state
## Already present in `ES-Workflow_template.json` → `# Control Pulses` (cells 44-119), for **both** `ge` and `ef` transitions, in this order
1. `## First Transition: g-e` / `## Second Transition: e-f`
2. `### Amplitude Rabi` (Experiment Parameters → Run Workflow via `amplitude_rabi.experiment_workflow` → Update Parameters)
3. `### Ramsey` (via `ramsey.experiment_workflow`)
4. `### T1 Lifetime` (via `lifetime_measurement.experiment_workflow`)
5. `### DRAG Calibration` (via `drag_q_scaling.experiment_workflow`) — **new, has no equivalent in the old notebook**
6. `### Hahn-Echo` (via `echo.experiment_workflow`)

Each block follows the same 3-step pattern: `#### Experiment Parameters` (builds `temporary_parameters` dict), `#### Run Workflow` (`options = X.experiment_workflow.options(); ...; workflow_result = exp_workflow.run()`), `#### Update Parameters` (reads `workflow_result.tasks["analysis_workflow"].output`, calls `X.update_qpu(...)`, optionally writes back to `qubit_to_measure.parameters` and calls `save(qpu, qpu_file_path)`).

Imports already include `resonator_spectroscopy(_amplitude)`, `qubit_spectroscopy`, `amplitude_rabi`, `ramsey`, `drag_q_scaling`, `lifetime_measurement`, `echo`, `dispersive_shift`, `iq_blobs` from `laboneq_applications.experiments`, plus helpers `set_transition()`, `log_sweep_help()`, `get_path_to_file()`.

## Present in old notebook's `# Control Pulse Setup` (cells 65-221) but **missing** from the new template
For `ge` (and mirrored for `ef`, minus one item):
* **Rabi Chevron / "Rabi Shevron"**: 2D sweep of drive detuning vs. Rabi drive amplitude, plotted as a 2D map. Built manually with `create_rabi(...)` + a `for` loop over detunings re-setting `drive_Oscillator_q0.frequency`.
* **Rabi Frequency Calibration** (`ge` only in the old notebook): sweeps drive-pulse *length* (not amplitude), fits a Rabi frequency for each length, then fits a line to `(1/length, extracted π-amplitude)` to get a slope/intercept relation. No workflow equivalent exists.
* **Rabi Error Amplification** (`x90` and `x180` sub-experiments): repeats a quantum operation `N` times to amplify small rotation-angle errors, fits the amplitude correction factor, and rescales `pi_amp`/`pihalf_amp`. This has a **direct Applications-Library equivalent**: `laboneq_applications.experiments.amplitude_fine`, with ready-made `experiment_workflow_x180` / `experiment_workflow_x90` (confirmed via LabOne Q docs) — not currently imported in the template.

Other old-notebook sections (`Set/Update x90 and x180 pulses`, manual power-range setting, manual `readout_low` dict, `.mat` saving of raw arrays) are artifacts of the manual pulse-library style and are already superseded by the template's `temporary_parameters`/`update_qpu` pattern — they are **not** re-implemented individually.

# Proposed changes
## Old → new parameter/variable name mapping (to be used throughout the new cells)
* `qubit_parameters["qb_freq"]` / `["qb_ef_freq"]` → `qubits[0].parameters.resonance_frequency_ge` / `resonance_frequency_ef`
* `qubit_parameters["qb_len"]` / `["qb_ef_len"]` → `ge_drive_length` / `ef_drive_length`
* `qubit_parameters["pi_amp"]` / `["pihalf_amp"]` (and `_ef_amp` variants) → `ge_drive_amplitude_pi` / `ge_drive_amplitude_pi2` (`ef_drive_amplitude_pi` / `ef_drive_amplitude_pi2`)
* `qubit_parameters["ro_amp"]`, `["relax"]` → `readout_amplitude`, `reset_delay_length`
* `lo_settings["qb_lo"]`, `["ro_lo"]` → `qubits[0].parameters.drive_lo_frequency`, `readout_lo_frequency`
* `n_average` (linear count) → `n_avg_exponent` (`count = 2**n_avg_exponent`), matching template convention
* `my_session` → `session`; manual `create_*`/`compile`/`run` → `X.experiment_workflow(...).run()`
* `.mat` saving via `get_path_to_file(figname, '.png', sample_parameters)` → template's `get_path_to_file(file_name, extension)` (directory defaults to `data_root_directory`)
* old `detuning_shev`/`detuning_ef` sweep arrays → new `chevron_detunings`; old `rabi_length_arr` → new `drive_lengths`

## New cells to add (Jupytext `# %%` cell markers), inserted after `Amplitude Rabi` and before `Ramsey` in each transition block, mirroring the old notebook's dependency order (coarse Rabi → chevron/characterization → fine amplitude calibration → other tune-up experiments)
For **both** `ge` and `ef` transitions:
1. `### Rabi Chevron` — implemented by looping the *existing* `amplitude_rabi.experiment_workflow` over a list of `temporary_parameters` with `resonance_frequency_ge/ef` shifted by each detuning value, collecting `workflow_result.tasks["run_experiment"].output` per detuning, then assembling/plotting a 2D map (amplitude × detuning). This keeps the "new workflow structure" instead of hand-building an `Experiment`.
2. `### Rabi Frequency Calibration` (`ge` and `ef`, extending the old notebook which only had `ge`) — loops `amplitude_rabi.experiment_workflow` over several `ge_drive_length`/`ef_drive_length` values (via `temporary_parameters`), reads the fitted π-amplitude from each `analysis_workflow_result.output`, fits `amplitude vs 1/length` to a line, and prints/saves the slope & intercept (kept as local variables / saved `.mat`, since `TunableTransmonQubit.parameters` has no dedicated field for this derived relation).
3. `### Rabi Error Amplification (Amplitude Fine)` — two `#### x180 pulse` / `#### x90 pulse` sub-sections, each using `amplitude_fine.experiment_workflow_x180` / `experiment_workflow_x90` with a `repetitions` sweep, following the identical `Experiment Parameters → Run Workflow → Update Parameters` 3-step pattern as the template's other experiments, calling `amplitude_fine.update_qpu(...)` to rescale `ge_drive_amplitude_pi`/`pi2` (or `ef_...`).

`amplitude_fine` needs to be added to the `from laboneq_applications.experiments import (...)` list (documented once at the top of the generated file as a reminder for the manual merge step).

## Deliverable
A single new file `workflows/control_pulse_setup.py` containing only these new cells (not the already-existing Amplitude Rabi/Ramsey/T1/DRAG/Echo cells), using `# %% [markdown]` / `# %%` Jupytext cell markers so it can be copy-pasted cell-by-cell into `ES-Workflow_template.json`. A short header comment in the file will point out where each block should be inserted, and the summary chat response will clearly enumerate which experiments already exist vs. which are new.