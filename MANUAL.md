# Library Function Reference Manual

Complete reference for every function, class, and constant in `lib/`.

---

## lib/helpers/setup_helper.py
Hardware descriptor and device calibration.

### Constants

- **`my_descriptor`** — YAML string defining the SHFQC instrument topology (device `DEV12192`). Maps five logical signal lines: `q0/drive_line`, `q0/drive_ef_line`, `q0/th_res_line`, `q0/measure_line`, `q0/acquire_line` to physical SGCHANNEL and QACHANNEL ports.

### Functions

#### `define_calibration(parameters, lo_settings)`
Creates a LabOne Q `Calibration` object from qubit parameter dictionaries.

- **parameters** `dict` — must contain keys: `qb_freq`, `qb_anharm`, `th_res_freq`, `ro_freq`, `ro_delay`, `ro_int_delay`.
- **lo_settings** `dict` — must contain keys: `qb_lo`, `ro_lo`.
- **Returns** `Calibration` — calibration for all five signal lines (drive, drive_ef, th_res, measure, acquire).

Oscillator assignments:
- `drive_line`: IF = `qb_freq`, HW modulation, LO = `qb_lo`
- `drive_ef_line`: IF = `qb_freq - qb_anharm`, HW modulation, LO = `qb_lo`
- `th_res_line`: IF = `th_res_freq`, HW modulation, LO = `qb_lo`
- `measure_line`: IF = `ro_freq`, SW modulation, LO = `ro_lo`
- `acquire_line`: IF = `ro_freq`, SW modulation, LO = `ro_lo`, with port delay = `ro_delay + ro_int_delay`

---

## lib/helpers/meas_helper_mod.py
Primary experiment factory — calibration builders, signal maps, and all `make_*` experiment constructors.

### Calibration Functions

#### `readout_calib(readout)`
- **readout** `dict` — keys: `measure_freq`, `acquire_freq`, `readout_range`, `readout_delay`.
- **Returns** `Calibration` — sets measure/acquire oscillators with SW modulation.

#### `long_readout_calib(readout)`
Same as `readout_calib` but uses HW modulation (for long-duration readouts).

#### `res_spec_calib(freq_sweep)`
- **freq_sweep** `SweepParameter` — frequency sweep for measure oscillator (HW modulation).
- **Returns** `Calibration` for spectroscopy mode.

#### `qubit_spec_calib(freq_sweep)`
Sets drive oscillator to `freq_sweep` with HW modulation.

#### `qubit_ef_spec_calib(freq_sweep)`
Sets `drive_ef` oscillator to `freq_sweep` with HW modulation.

#### `make_ramsey_calib(freq, detuning)`
Sets drive oscillator to `freq + detuning` (HW modulation).

#### `make_ramsey_ef_calib(freq, detuning)`
Sets `drive_ef` oscillator to `freq + detuning` (HW modulation).

#### `make_th_res_calib(th_res_freq, qb_freq, detuning)`
Sets `th_res` oscillator to `th_res_freq` and drive oscillator to `qb_freq + detuning`.

#### `make_fast_flux_calib(th_res_freq, qb_freq, detuning, lo_freq)`
Same as above but also sets the drive LO to `lo_freq`.

### Signal Map Constants

- **`MA_map`** — measure + acquire only (for resonator spectroscopy without qubit drive).
- **`qubit_meas_map`** — drive + measure + acquire (standard g-e experiments).
- **`qubit_ef_only_map`** — drive_ef + measure + acquire (e-f spectroscopy without g-e drive).
- **`qubit_ef_map`** — drive + drive_ef + measure + acquire (experiments involving both transitions).
- **`qubit_resonator_map`** — drive + th_res + measure + acquire (flux/thermal resonator experiments).
- **`qubit_all_map`** — drive + drive_ef + th_res + measure + acquire (all signal lines).

### Pulse Constants

- **`readout_pulse_def`** — default readout pulse (constant, 2 µs, amplitude 0.6).
- **`readout_weighting_function_def`** — default integration kernel (constant, 2 µs, amplitude 1.0).

### Core Building Blocks

#### `readoutQubit(exp, section_id, readout_id, acquire_id, acquire_handle, play_after_section, reserve_id, readout_pulse, readout_weights, relax_time, delay_uid, acquire_length)`
Appends a readout+acquisition+relaxation section to an existing experiment. Used by all `make_*` functions.

- **exp** `Experiment` — experiment to modify (in-place).
- **section_id** `str` — UID of the readout section (default: `"qubit_readout"`).
- **readout_id** / **acquire_id** `str` — signal names for measure/acquire.
- **acquire_handle** `str` — data handle for retrieved results.
- **play_after_section** `str|None` — section ordering constraint.
- **reserve_id** `str|None` — if set, reserves this signal during readout.
- **relax_time** `float` — delay after readout for qubit relaxation (default: 20 µs).
- **delay_uid** `str` — UID for the delay section (default: `"delay"`).
- **acquire_length** `float|None` — explicit acquisition length (overrides kernel length).

#### `long_readout_qubit(...)`
Stub for compressible long readout pulses. Asserts `readout_pulse.can_compress`. (Implementation incomplete.)

#### `make_two_point_sweep(start=0.0, stop=1.0)`
Returns a `LinearSweepParameter` with count=2, used for population measurement sweep points.

### Spectroscopy Experiments

#### `res_spectroscopy(freq_sweep, readout_pulse_spec, n_average)`
Pulsed resonator spectroscopy. Sweeps readout frequency in near-time, acquires in SPECTROSCOPY mode.
- **Returns** `Experiment` — handles: `"res_spec"`.

#### `qubit_spectroscopy(freq_sweep, qubit_pulse, readout_pulse, readout_weighting_function, relax_time, n_average)`
Pulsed qubit spectroscopy (g-e). Near-time frequency sweep on drive, INTEGRATION acquisition.
- **Returns** `Experiment` — handles: `"q0_spec"`.

#### `qubit_ef_spectroscopy(freq_sweep, qubit_pulse, readout_pulse, readout_weighting_function, relax_time, n_average)`
Pulsed qubit spectroscopy on the e-f transition (no g-e prepulse).
- **Returns** `Experiment` — handles: `"q0_ef_spec"`.

#### `qubit_ef_spectroscopy_with_prepulse(freq_sweep, x180, qubit_pulse, readout_pulse, readout_weighting_function, relax_time, n_average)`
e-f spectroscopy with a π(g-e) prepulse to populate |e⟩ before probing e-f.
- **Returns** `Experiment` — handles: `"q0_ef_spec"`.

#### `make_res_spec_e(freq_sweep, x180, readout_pulse, readout_weighting_function, relax_time, n_average, ge_amp)`
Resonator spectroscopy with optional π(g-e) prepulse. Set `ge_amp=0` for |g⟩, `ge_amp=1` for |e⟩.
- **Returns** `Experiment` — handles: `"q0_res_spec_e"`.

#### `make_res_spec_f(freq_sweep, x180, x180_ef, readout_pulse, readout_weighting_function, relax_time, n_average)`
Resonator spectroscopy with π(g-e) + π(e-f) prepulses to measure in |f⟩.
- **Returns** `Experiment` — handles: `"q0_res_spec_f"`.

#### `make_res_spec_flux(freq_sweep, flux_pulse, x180, readout_pulse, readout_weighting_function, relax_time, n_average, ge_amp)`
Resonator spectroscopy with concurrent flux pulse on `th_res` signal.
- **Returns** `Experiment` — handles: `"q0_res_spec_flux"`.

### g-e Transition Experiments

#### `make_rabi(rabi_sweep, gaussian_pulse, readout_pulse, readout_weighting_function, relax_time, n_average)`
Amplitude Rabi experiment: sweeps drive amplitude.
- **Returns** `Experiment` — handles: `"q0_rabi"`.

#### `make_rabi_SS(rabi_sweep, gaussian_pulse, readout_pulse, readout_weighting_function, relax_time, n_average)`
Single-shot Rabi experiment (SINGLE_SHOT averaging).
- **Returns** `Experiment` — handles: `"SS_rabi"`.

#### `make_pulse_repetition(pulse, N_sweep, readout_pulse, readout_weighting_function, relax_time, n_average)`
Repeats a pulse N times before readout (N is swept).
- **Returns** `Experiment` — handles: `"q0_rep"`.

#### `make_shots(state, x_180, x_180_ef, readout_pulse, readout_weighting_function, relax_time, n_average)`
Single-shot state preparation and measurement.
- **state** `str` — `'g'`, `'e'`, or `'f'`. Prepares the qubit in that state before readout.
- **Returns** `Experiment` — handles: `"shots"`.

#### `make_t1(t1_sweep, x180, readout_pulse, readout_weighting_function, relax_time, n_average)`
T1 relaxation measurement: π pulse → variable delay → readout.
- **Returns** `Experiment` — handles: `"q0_t1"`.

#### `make_ramsey(ramsey_sweep, x90, readout_pulse, readout_weighting_function, relax_time, n_average)`
Ramsey experiment: π/2 → variable delay → π/2 → readout. Measures T2* / frequency detuning.
- **Returns** `Experiment` — handles: `"q0_ramsey"`.

#### `make_echo(echo_sweep, x90, x180, readout_pulse, readout_weighting_function, relax_time, n_average)`
Hahn echo: π/2 → τ → π → τ → π/2 → readout. Measures T2.
- **Returns** `Experiment` — handles: `"q0_echo"`.

### e-f Transition Experiments

#### `make_rabi_ef_1(rabi_ef_sweep, gaussian_pulse, readout_pulse, readout_weighting_function, relax_time, n_average, x180, ge_amp=0.0)`
Amplitude Rabi on e-f with ONE g-e prepulse. Set `ge_amp=1.0` to populate |e⟩ first.
- **Returns** `Experiment` — handles: `"q0_rabi_ef"`.

#### `make_rabi_ef_2(rabi_ef_sweep, gaussian_pulse, readout_pulse, readout_weighting_function, relax_time, n_average, x180, ge_amp=0.0)`
Same but with TWO g-e pulses (sandwich): π(g-e) → θ(e-f) → π(g-e) → readout.
- **Returns** `Experiment` — handles: `"q0_rabi_ef"`.

#### `make_T1_ef_1(t1_ef_sweep, x180_ef, readout_pulse, readout_weighting_function, relax_time, n_average, x180, ge_amp=0.0)`
T1 measurement on the e-f transition: optional π(g-e) → π(e-f) → variable delay → readout.
- **Returns** `Experiment` — handles: `"q0_t1_ef"`.

#### `make_ramsey_ef_2(ramsey_ef_sweep, x90_ef, readout_pulse, readout_weighting_function, relax_time, n_average, x180, ge_amp=0.0)`
Ramsey on e-f with two g-e sandwich pulses: π(g-e) → π/2(e-f) → τ → π/2(e-f) → π(g-e) → readout.
- **Returns** `Experiment` — handles: `"q0_ramsey_ef"`.

### Population Measurement Experiments

#### `make_exp_population(x180, x180_ef, readout_pulse, readout_weighting_function, relax_time, n_average)`
Basic population measurement using nested 2-point sweeps. Acquires two readout handles per iteration.
- **Returns** `Experiment` — handles: `"first_readout"`, `"second_readout"`.

#### `make_exp_population_full(x180, x180_ef, readout_pulse, readout_weighting_function, relax_time, n_average)`
Full three-level population measurement. Runs six sequential pulse+readout sequences (x0, x1, x2, y0, y1, y2) in a single averaging loop.

Pulse sequences:
- **x0**: readout only (no drive)
- **x1**: π(g-e) → readout
- **x2**: π(g-e) → π(e-f) → readout
- **y0**: π(e-f) → readout
- **y1**: π(e-f) → π(g-e) → readout
- **y2**: π(e-f) → π(g-e) → π(e-f) → readout

- **Returns** `Experiment` — handles: `"x0_readout"`, `"x1_readout"`, `"x2_readout"`, `"y0_readout"`, `"y1_readout"`, `"y2_readout"`.

#### `make_exp_population_flux(x180, x180_ef, flux_pulse, readout_pulse, readout_weighting_function, relax_time, n_average)`
Same six-point sequence but with a flux pulse played during each relaxation interval.
- **Returns** `Experiment` — same handles as `make_exp_population_full`.

#### `make_exp_pop_correlations(x180, r_delay, readout_pulse, readout_weighting_function, relax_time, n_average)`
Population correlation measurement: two consecutive readouts (with variable delay `r_delay`), then π pulse + two more readouts. SINGLE_SHOT averaging.
- **Returns** `Experiment` — handles: `"readout_1"`, `"readout_2"`, `"readout_pi1"`, `"readout_pi2"`.

#### `make_exp_pop_correlation_continuous_ro(...)`
Placeholder. Raises `NotImplementedError`.

#### `make_exp_population_prepulse(pulse_sweep, x180, x180_ef, gaussian_pulse, readout_pulse, readout_weighting_function, relax_time, n_average)`
Full six-point population measurement with a swept-amplitude prepulse before each sequence.
- **Returns** `Experiment` — same x0–y2 handles.

### Rabi Population Measurement (RPM)

#### `get_rabi_population_calibration_measurement(theta_ef_sweep, gaussian_pulse, readout_pulse, readout_weighting_function, relax_time, n_average, x180)`
Full RPM calibration: sweeps e-f rotation angle θ, acquires two sets (without and with g-e prepulse).
- **Returns** `Experiment` — handles: `"rpm_wo"`, `"rpm_with"`.

#### `get_quick_rabi_population_measurement(rpm_x180_ef_pulse, rep_count, gaussian_pulse, readout_pulse, readout_weighting_function, relax_time, n_average, x180)`
Quick RPM: measures only min/max points (4 readouts per iteration), repeated `rep_count` times.
- **Returns** `Experiment` — handles: `"rpm_wo_min"`, `"rpm_wo_max"`, `"rpm_with_min"`, `"rpm_with_max"`.

### Thermal Resonator / Fast Flux Experiments

#### `make_th_res_amp(res_amp_sweep, gaussian_pulse, x180, readout_pulse, readout_weighting_function, relax_time, n_average, delay_time=1e-6)`
Sweeps thermal resonator pulse amplitude, then applies π(g-e) + delay + readout.
- **Returns** `Experiment` — handles: `"q0_tr_amp"`.

#### `make_th_res_decay(t1_sweep, th_res_pulse, x180, readout_pulse, readout_weighting_function, relax_time, n_average)`
T1 measurement while pumping the thermal resonator.
- **Returns** `Experiment` — handles: `"q0_tr_decay"`.

#### `make_th_res_ramsey(ramsey_sweep, th_res_pulse, x90, readout_pulse, readout_weighting_function, relax_time, n_average)`
Ramsey experiment while pumping the thermal resonator.
- **Returns** `Experiment` — handles: `"q0_tr_ramsey"`.

#### `make_fast_flux_decay(t1_sweep, flux_pulse, edge, x180, readout_pulse, readout_weighting_function, relax_time, n_average)`
Qubit decay measurement while detuned by a fast flux pulse of variable length.
- **Returns** `Experiment` — handles: `"q0_ff_decay"`.

### Calibration / Diagnostics

#### `make_propagation_delay(delay_sweep, readout_pulse, acquire_length, relax_time, n_average)`
Sweeps the acquisition port delay to find the optimal readout integration timing.
- **Returns** `Experiment` — handles: `"res_prop_delay"`.

#### `repeat(count, exp)`
Decorator/helper that repeats a section of an experiment `count` times (supports both integer and `SweepParameter`).

#### `make_rabi_error_amplification(flips_sweep, x180, x90, readout_pulse, readout_weighting_function, relax_time, n_average, target_pulse)`
Amplifies Rabi pulse errors by repeating the target pulse many times.
- **target_pulse** `str` — `'x90eg'` or `'x180eg'`.
- **Returns** `Experiment` — handles: `"calib_0"`, `"calib_1"`, `"q0_rabi"`.

#### `make_rabi_error_amplification_ef(flips_sweep, x180, x90, x180ef, x90ef, readout_pulse, readout_weighting_function, relax_time, n_average, target_pulse)`
Same for e-f pulses.
- **target_pulse** `str` — `'x90ef'` or `'x180ef'`.
- **Returns** `Experiment` — handles: `"calib_0"`, `"calib_1"`, `"q0_rabi"`.

#### `make_readout_single_shot(readout_pulse, readout_weighting_function, relax_time, n_average)`
Single-shot readout with no qubit drive (for noise floor / thermal population).
- **Returns** `Experiment` — handles: `"shots"`.

#### `make_flux_pulse_testing(flux_pulse, n_average, rep_sweep, delay_time=1e-6, amplitude=1)`
Flux pulse diagnostic with repeated playback for oscilloscope monitoring.

---

## lib/helpers/meas_helper_mod_2.py
Near-duplicate of `meas_helper_mod.py` with minor differences (e.g. `make_flux_pulse_testing` has no `rep_sweep`, `make_propagation_delay` uses `readout_pulse.length`). Provides the same categories: calibration builders, signal maps, readoutQubit, and all experiment constructors. Refer to `meas_helper_mod.py` above for semantics — function signatures and behaviour are nearly identical.

Additional unique function:
#### `make_flux_pulse_testing(flux_pulse, n_average, delay_time=1e-6, amplitude=1)`
Simpler variant: plays a single flux pulse + delay, no sweep or qubit drive.

---

## lib/helpers/create_meas_helper.py
Convenience wrappers that call `meas_helper_mod` builders, then auto-apply calibration and signal map. Every `create_*` function returns a ready-to-compile `Experiment`.

#### `create_rabi(rabi_sweep, gaussian_pulse, readout, n_average)`
Wraps `make_rabi`. Applies `readout_calib` + `qubit_meas_map`.

#### `create_rabi_SS(rabi_sweep, gaussian_pulse, readout, n_average)`
Wraps `make_rabi_SS`.

#### `create_SS(state, x_180, x_180_ef, readout, n_average)`
Wraps `make_shots`. Uses `qubit_ef_map`.

#### `create_rabi_ef(rabi_ef_sweep, gaussian_pulse, readout, n_average, x180, ge_amp=0.0, n_ge_pulses=1)`
Wraps `make_rabi_ef_1` or `make_rabi_ef_2` based on `n_ge_pulses`.

#### `create_t1(t1_sweep, x180, readout, n_average)`
Wraps `make_t1`.

#### `create_T1_ef_1(t1_ef_sweep, x180_ef, readout, n_average, x180, ge_amp=0.0)`
Wraps `make_T1_ef_1`.

#### `create_ramsey(ramsey_sweep, x90, readout, n_average, parameters)`
Wraps `make_ramsey`. Also applies `make_ramsey_calib` using `parameters["qb_freq"]` and `parameters["ramsey_det"]`.

#### `create_ramsey_ef(ramsey_ef_sweep, x90_ef, readout, n_average, x180, parameters, ge_amp=0.0)`
Wraps `make_ramsey_ef_2`. Applies `make_ramsey_ef_calib`.

#### `create_echo(echo_sweep, x90, x180, readout, n_average)`
Wraps `make_echo`.

#### `create_exp_population_full(x180, x180_ef, readout, n_average)`
Wraps `make_exp_population_full`. Uses `qubit_ef_map`.

#### `create_exp_population_flux(x180, x180_ef, flux_pulse, readout, n_average)`
Wraps `make_exp_population_flux`. Uses `qubit_all_map`.

#### `create_exp_population_correlations(x180, r_delay, readout, n_average)`
Wraps `make_exp_pop_correlations`.

#### `create_qubit_spec(freq_sweep_TT, square_pulse, readout, n_average)`
Wraps `qubit_spectroscopy`. Applies `qubit_spec_calib`.

#### `create_qubit_ef_spec(freq_sweep_ef, square_pulse, readout, n_average)`
Wraps `qubit_ef_spectroscopy`. Uses `qubit_ef_only_map`.

#### `create_qubit_ef_spec_prep(freq_sweep_ef, x180, square_pulse, readout, n_average)`
Wraps `qubit_ef_spectroscopy_with_prepulse`.

#### `create_res_spec_gef(freq_sweep, x180, x180_ef, readout, n_average, level=0)`
Resonator spectroscopy for state |g⟩ (`level=0`), |e⟩ (`level=1`), or |f⟩ (`level=2`).

#### `create_prop_delay(delay_sweep, readout_pulse, acquire_length, relax_time, n_average)`
Wraps `make_propagation_delay`.

#### `create_rabi_error_amp(flips_sweep, x180, x90, readout, n_average, target_pulse)`
Wraps `make_rabi_error_amplification`.

#### `create_rabi_error_amp_ef(flips_sweep, x180, x90, x180ef, x90ef, readout, n_average, target_pulse)`
Wraps `make_rabi_error_amplification_ef`.

#### `create_readout_single_shot(readout, n_average)`
Wraps `make_readout_single_shot`.

---

## lib/helpers/fitting_helper.py
Curve-fitting models, fitting routines, and data processing utilities.

### Model Functions

#### `func_lin(x, a, b)` → `a*x + b`
#### `func_parabola(x, a, b, c)` → `a*x² + b*x + c`
#### `func_osc(x, freq, phase, amp=1, off=0)` → `amp * cos(freq*x + phase) + off`
#### `func_decayOsc(x, freq, phase, rate, amp=1, off=-0.5)` → `amp * cos(freq*x + phase) * exp(-rate*x) + off`
#### `func_double_decayOsc_2amps(x, freq, dfreq, phase, rate, amp=1, amp2=0.1, off=-0.5)` → Two-frequency decaying oscillation.
#### `func_exp(x, rate, off, amp=1)` → `amp * exp(-rate*x) + off`
#### `func_two_exp(x, rate1, rate2, off, A, B)` → `A*exp(-rate1*x) + B*exp(-rate2*x) + off`
#### `func_lorentz(x, width, pos, amp, off)` → Lorentzian peak.
#### `func_invLorentz(x, width, pos, amp, off=1)` → Inverted Lorentzian (dip).
#### `func_Fano(x, width, pos, amp, fano=0, off=0.5)` → Fano lineshape.
#### `gauss(x, mu, sigma, A)` → Gaussian.
#### `bimodal(x, mu1, sigma1, A1, mu2, sigma2, A2)` → Sum of two Gaussians.

### Fit Wrappers
All return `(popt, pcov)` — optimized parameters and covariance matrix.

#### `fit_linear(x, y, plot=False)` — Linear fit.
#### `fit_Rabi(x, y, freq, phase, amp=None, off=None, plot=False, bounds=None)` — Cosine oscillation.
#### `fit_osc_fixed_amp_phase(x, y, freq, fixed_phase, fixed_amp, off=None)` — Oscillation with fixed amplitude/phase, fit freq+offset only.
#### `fit_Ramsey(x, y, freq, phase, rate, amp=None, off=None, plot=False, bounds=None)` — Decaying oscillation.
#### `fit_double_Ramsey_2amps(time, trace, freq, dfreq, phase, rate, amp, amp2, off, plot, bounds, zero_ind)` — Two-frequency decaying oscillation. Auto-rotates IQ trace.
#### `fit_T1(x, y, rate, off, amp=None, plot=False, bounds=None)` — Exponential decay.
#### `fit_T1_ef(x, y, rate1, rate2, off, A=0.1, B=0.1, plot=False, bounds=None)` — Double exponential (for e-f decay).
#### `fit_Spec(x, y, width, pos, amp, off=None, plot=False, bounds=None)` — Inverted Lorentzian.
#### `fit_3DSpec(x, y, width, pos, amp, off=None, plot=False, bounds=None)` — Lorentzian peak.
#### `fit_ResSpec(x, y, width, pos, amp, fano, off=None, plot=False, bounds=None)` — Fano lineshape.

### Auto-Fit Functions
Automatically estimate initial parameters and fit.

#### `auto_T1_fit(t1_delay, t1_data, data_type='real', plot=False)`
- **data_type** `str` — `'real'`, `'imag'`, `'amp'`, `'phase'`, `'rot'`.
- **Returns** `(popt_arr, pcov_arr)` — shape `(N, 3)` and `(N, 3, 3)` where N = number of traces. Parameters: `[rate, offset, amplitude]`.

#### `auto_ramsey_fit(ramsey_delay, ramsey_data, data_type='real', plot=False)`
Uses FFT to find initial frequency estimate.
- **Returns** `(popt_arr, pcov_arr)` — parameters: `[freq, phase, rate, amp, off]`.

#### `auto_ramsey_fit_freq(ramsey_delay, ramsey_data, data_type='real', plot=False)`
Fits the FFT spectrum instead of the time trace. Returns `[width, position, amplitude, offset]`.

#### `auto_echo_fit(echo_delay, echo_data, data_type='phase', plot=False)`
Wrapper around `auto_T1_fit` with `echo_delay*2`.

### FFT and Peak Detection

#### `FFT_analize(x, y, plot=False)`
Computes FFT of `y`. Returns `(fx, fy)` — frequency axis and complex FFT.

#### `find_pick_param(x, y, sign=1)`
Finds peak position, index, half-width, amplitude, and offset. `sign=1` for max, `-1` for min.
- **Returns** `(x0, opt_x, wx, y0, off)`.

#### `fit_FFT_spec(fx, fy, plot=False)`
Fits FFT magnitude with an inverted Lorentzian.

### Data Processing

#### `find_rotation(data, plot=False)` — Finds IQ rotation angle via linear fit. Returns `angle` (radians).
#### `rotate_and_norm(data, norm=False)` — Rotates complex data to align with real axis. Optionally normalizes to [0,1].
#### `reshape_to_1D(x)` / `reshape_to_2D(x)` — Shape utilities.
#### `average_by_key(data, markers)` — Averages dict entries sharing a key prefix.
#### `average_by_N(arr1D, N)` — Bins a 1D array in groups of N.
#### `stretch_by_N(arr1D, N)` — Repeats each element N times.
#### `transform_complex_to_real(data, data_type='real')` — Converts complex data to real using `data_type`: `'amp'`, `'phase'`, `'real'`, `'imag'`, `'rot'`.

### PCA

#### `normalize_1d_osc(osc, offset=None, norm=None)`
Normalizes oscillation data to [-1, 1] range.

#### `compute_pca(i_data, q_data, plot=True, scaling_fac=0.1)`
PCA decomposition of IQ data.
- **Returns** dict with keys: `pca`, `comp_1_I`, `comp_1_Q`, `comp_2_I`, `comp_2_Q`, optionally `fig_ax`.

#### `get_qrpm_dict_from_list_of_results(results)`
Extracts I/Q/mag/phase min/max arrays from a list of quick RPM result dicts.

### Plotting

#### `plot_result_2d(results, handle, mult_axis=None)` — 2D plot of experiment results.
#### `plot_result_3d(results, handle)` — 3D wireframe of 2D sweep results.
#### `plot2d_abs(results, handle)` — Quick magnitude plot.

### Error Analysis

#### `abs_err(pcov)` — Absolute errors from covariance matrix diagonal.
#### `rel_err(popt, pcov)` — Relative errors.
#### `check_reload()` — Prints confirmation message (debugging aid).

---

## lib/helpers/pop_temp_helper.py
Temperature extraction (two-level approximation).

#### `T_calc(C, f_q)` — Temperature from Boltzmann ratio C = p_e/p_g at qubit frequency f_q. Returns T in units matching f_q (GHz → millikelvin when multiplied by 1e3).
#### `get_ABC(pop_proj)` — Computes 9 ABC population ratios from projected data dict (keys: `x0`–`x2`, `y0`–`y2`). Returns dict with keys `A1,B1,C1,A2,B2,C2,A3,B3,C3`.
#### `make_projection(pop_full_results, phase)` — Rotates complex results by `phase`, returns `(res_I, res_Q)` dicts.
#### `get_temperature(ABC, f_q)` — Converts ABC → effective temperatures using the **two-level** model only.
#### `get_stat(data)` — For each key: returns `[mean, std, relative_error]`.

---

## lib/helpers/pop_temp_helper_v2.py
Temperature extraction (three-level model).

### Constants
- **`pop_label_list`** = `['x0', 'x1', 'x2', 'y0', 'y1', 'y2']`

### Temperature Model Functions

#### `T_calc(C, f_q)` — Same as v1.
#### `A_temp(T, A, f_q, anharm)` — Residual function for A-type temperature equation (three-level model). Used with `fsolve`.
#### `B_temp(T, B, f_q, anharm)` — Residual for B-type.
#### `C_temp(T, C, f_q, anharm)` — Residual for C-type.

### Core Functions

#### `get_ABC(pop_proj)` — Same as v1.
#### `make_projection(pop_full_results, phase)` — Same as v1.
#### `get_temperature(ABC, f_q, anharm, three_levels=False)`
- When `three_levels=True`: uses `scipy.optimize.fsolve` with `A_temp/B_temp/C_temp` for the full three-level model.
- When `three_levels=False`: falls back to the two-level approximation.
- **Returns** dict with keys `TA1, TB1, TC1, ...`.

#### `get_stat(data)` — Returns `np.array([mean, std, rel_err])` per key.
#### `get_stat_nan(data)` — Same but uses `nanmean`/`nanvar`.

### Pipeline Functions

#### `make_all_temperatures(pop_full_results, f_q, anharm, phase=0, three_levels=True)`
Complete pipeline: project → ABC → temperature for both I and Q components.
- **Returns** `(TABC_I, TABC_Q)`.

#### `make_rotation_temperature(data, phase_arr, f_q, anharm, three_levels=True)`
Sweeps projection phase, computes temperature statistics at each angle.
- **Returns** `(STAT_I, STAT_Q)` — dicts of arrays shaped `(len(phase_arr), 3)`.

#### `make_optimal_temperature(data, phase_arr, f_q, anharm, skip=[], info_type='rel_err', three_levels=True)`
Finds the projection phase and ABC method that minimizes the chosen error metric.
- **Returns** dict: `{'rel_err', 'phase', 'ph_p', 'method', 'axes'}`.

#### `find_optimal_temperature(pop_full_results, optimal_method, f_q, anharm, three_levels=True)`
Extracts temperature using the optimal method/phase found above.
- **Returns** temperature array.

### Alternative Processing (Parallel Approach)

#### `get_diff(pop_proj)` — Computes pairwise differences of x0–y2 projections. Returns 9-entry dict.
#### `get_axes_and_rotate(D1, D2, D3)` — Auto-rotates complex differences to extract A, B, C ratios.
#### `get_ABC_parallel(pop_full_results)` — Full pipeline for the parallel approach. Returns ABC dict.
#### `get_C_from_ABC(ABC_dict)` — Converts all A/B/C ratios to the C-equivalent form.

### Plotting

#### `plot_temperatures(TABC_I, TABC_Q, skip=[], xlim=None, ylim=None)` — Dual-panel I/Q temperature plot.
#### `plot_temp_single(TABC, skip=[], xlim=None, ylim=None, xdata=None, xlabel='Point Number')` — Single-panel temperature plot. Returns `(fig, ax)`.
#### `plot_rotation_stat(phase_arr, STAT_I, STAT_Q, info_type='rel_err')` — 3×3 grid of temperature vs. phase plots for all 9 ABC parameters.
#### `plot_stat(STAT_I, STAT_Q, element=0)` — Bar chart of temperature statistics with error bars.

---

## lib/helpers/save_data_helper.py
Data persistence utilities.

#### `get_path(sample_parameters)` — Builds date-stamped folder path: `<folder>/<sample>/<structure>/YYYY-MM-DD Jupiter/`.
#### `get_path_to_file(name, form, sample_parameters)` — Returns timestamped filename in the date folder.
#### `save_data(data_name, data, sample_parameters, qubit_parameters, lo_settings)` — Merges parameter dicts into data and saves as `.mat`.

---

## lib/helpers/feedback_helper.py
Helpers for state discrimination and real-time feedback.

#### `complex_freq_phase(sampling_rate, length, freq, amplitude=1.0, phase=0.0)`
Generates a complex-valued readout waveform with software modulation.
- **Returns** `np.ndarray` — complex samples.

#### `exp_raw(measure_pulse, q0, pulse_len)`
Raw signal acquisition experiment (1024 shots, RAW mode).
- **Returns** `Experiment` — handles: `"raw"`.

#### `exp_integration(measure0, measure1, q0, q1, samples_kernel, rotation_angle=0)`
Single-shot integration with custom kernel, acquires two states sequentially.
- **Returns** `Experiment` — handles: `"data0"`, `"data1"`.

#### `exp_discrimination(measure0, measure1, q0, q1, samples_kernel, threshold=0, rotation_angle=0, num=50)`
State discrimination test using DISCRIMINATION acquisition type.
- **Returns** `Experiment` — handles: `"data0"`, `"data1"`.

---

## lib/helpers/randomized_benchmarking_helper.py
Single-qubit randomized benchmarking (RB).

#### `pulse_envelope(amplitude, pulse_length, phase, sigma, sample_rate)`
Samples a Gaussian pulse with given phase. Returns `np.ndarray` of shape `(N, 2)` — real and imaginary parts.

#### `basic_gate_set(pi_amp, pi_2_amp, gate_time, sigma, sample_rate)`
Creates the fundamental gate set: `{I, X, Y, X/2, Y/2, -X/2, -Y/2}`.
- **Returns** dict of sampled pulse arrays.

#### `basic_pulse_set(gate_set)`
Converts gate arrays to LabOne Q `sampled_pulse_complex` objects.

### Clifford Algebra

- **`clifford_parametrized`** — 24 Clifford gates decomposed into Pauli rotations.
- **`elem_gates`** — 2×2 matrix representations of `{I, X, Y, X/2, Y/2, -X/2, -Y/2}`.
- **`clifford_matrices`** / **`clifford_gates`** — matrix representations of all 24 Cliffords.

#### `pauli(axis)` — Returns Pauli matrix for `"x"`, `"y"`, or `"z"`.
#### `rot_matrix(angle=π, axis="x")` — General SU(2) rotation matrix.
#### `mult_gates(gate_list, use_linalg=False)` — Matrix product of a list of gates.
#### `glob_phase(phase, dim=2)` — Global phase operator.
#### `match_up_to_phase(target, gate_list, dim=2)` — Finds best-matching gate up to global phase.
#### `calculate_inverse_clifford(seq_list, clifford_list)` — Computes the recovery gate index for a Clifford sequence.
#### `generate_play_rb_pulses(exp, signal, seq_length, cliffords, pulse_set)` — Generates and plays a random RB sequence (including recovery gate) on a signal line.

---

## lib/helpers/example_notebook_helper.py
Self-contained helper used by example/tutorial notebooks. Contains duplicates of `fitting_helper.py` functions plus simulation plotting.

#### `plot_simulation(compiled_experiment, start_time=0.0, length=10e-6, ...)` — Plots simulated I/Q waveforms from a compiled experiment using `OutputSimulator`.

All other functions (`plot_result_2d/3d`, `plot2d_abs`, `func_*`, `fit_*`, `auto_*_fit`, `FFT_analize`, `normalize_1d_osc`, `compute_pca`, `get_qrpm_dict_from_list_of_results`, `check_reload`) — identical to `fitting_helper.py`.

---

## lib/helpers/example_notebook_simple.py
Minimal calibration example for a two-qubit device setup.

#### `calibrate_devices(device_setup)` — Applies default calibration to `q0` and `q1` logical signal groups (drive, flux, measure, acquire lines).
#### `create_device_setup(generation=2)` — Loads a device descriptor YAML and returns a calibrated `DeviceSetup`. `generation=1` for HDAWG+UHFQA, `generation=2` for SHFSG+SHFQA.

---

## lib/devices/YokoGS200_wrapper.py
### Class `YokoGS200`
Wrapper for the Yokogawa GS200 DC source via PyVISA.

- **`__init__(address)`** — VISA address string.
- **`open_inst()` / `close_inst()`** — Open/close VISA resource.
- **`set_func(func)`** — Set output function (`'VOLT'` or `'CURR'`).
- **`get_func()`** — Query current function.
- **`set_output(state)`** — Enable (`True`) or disable (`False`) output.
- **`get_output()`** — Query output state.
- **`set_protect(func, rng)`** — Set voltage/current protection limit.
- **`get_protect(func)`** — Query protection limit.
- **`set_level(level)`** — Set output level.
- **`get_level(only_number=False)`** — Query level. Returns float when `only_number=True`.
- **`set_range(rng)`** / **`get_range()`** — Set/query output range.
- **`ramp(value, N_steps=1e3)`** — Linear ramp from current level to `value` in `N_steps`.

---

## lib/devices/SIM_wrapper.py
### Class `SIM900`
Wrapper for SRS SIM900 mainframe.

- **`__init__(address)`**
- **`open_inst()` / `close_inst()`** — VISA resource management.
- **`write_inst(cmd)` / `query_inst(qry)`** — Send SCPI commands.
- **`get_sim(port)`** — Returns a `SIM928` object for the specified slot (1–8).

### Class `SIM928`
Wrapper for SIM928 voltage source modules inside a SIM900.

- **`__init__(frame, port)`** — `frame` is the parent `SIM900`.
- **`open_sim()` / `close_sim()`** — Connect/disconnect to the specific port.
- **`set_output(state)`** / **`get_output()`** — Enable/disable/query output.
- **`set_level(level)`** — Set voltage (with overflow protection at `vlimit=20V`).
- **`get_level(only_number=False)`** — Query voltage.
- **`ramp(value, N_steps=1e3)`** — Linear ramp.
- **`rampto(val)`** — Rate-limited ramp at `self.ramprate` V/s.

---

## lib/devices/KeysightDMM34465A.py
### Class `KeysightDMM34465A`
Wrapper for Keysight 34465A digital multimeter.

- **`__init__(address)`**
- **`open_inst()` / `close_inst()`**
- **`get_id()`** — Query `*IDN?`.
- **`get_nplc()` / `set_nplc(nplc)`** — Number of power line cycles (integration time).
- **`get_range()` / `set_range(value)`** — Voltage range.
- **`scan()`** — Single voltage reading. Returns string.
- **`conf_trig()` / `get_trig()` / `set_trig(value)`** — Trigger source config.
- **`init_trig()` / `bus_trig()`** — Initiate / trigger measurement.
- **`get_sample_count()`** — Query sample count.
- **`local()` / `reset()`** — Return to local mode / factory reset.

---

## lib/devices/KeysightWG33622A.py
### Class `KeysightWG33622A`
Wrapper for Keysight 33622A waveform generator.

- **`__init__(address)`**
- **`open_inst()` / `close_inst()`**
- **`set_func(func)` / `get_func()`** — Output function.
- **`set_output(state)` / `get_output()`** — Enable/disable.
- **`set_protect(func, rng)` / `get_protect(func)`** — Protection limits.
- **`set_level(level)` / `get_level(only_number=False)`** — Channel 1 voltage.
- **`set_freq(freq)` / `get_freq(only_number=False)`** — Channel 1 frequency.
- **`set_range(rng)` / `get_range()`** — Output range.
- **`ramp(value, N_steps=1e3)`** — Linear ramp.

---

## lib/devices/XLD_Server_Client.py
### Class `XLDMeasClient`
HTTP client for coordinating measurements with a BlueFors XLD dilution refrigerator.

- **`__init__(server_ip, user, group, server_port=8080, update_interval=30)`**
- **`open_session()`** — Register with the server, wait for sweep info broadcast. Returns `(n_sweep, timeout)`.
- **`close_session()`** — Deregister.
- **`listen(autostart=True)`** — Poll for `"go"` signal. Returns `True` when received.
- **`started()` / `stopped()`** — Notify server of measurement status.
- **`get_mxc_temp()`** — Query mixing chamber temperature. Returns float.

---

## lib/utils/calculator.py
Physics utility functions and resonator analysis classes.

### Physical Constants
`e`, `kb`, `Delta` (superconducting gap), `h_bar`, `h`, `GHz` = 1e9.

### Transmon Parameters

#### `n_10(EJ, EC)` — Charge matrix element ⟨1|n̂|0⟩ = √(1/2) × (EJ/8EC)^0.25.
#### `chi(g, delta, Ec)` — Dispersive shift: -g²Ec / [δ(δ-Ec)].
#### `chi_i(g_i, delta_i)` — Level-specific dispersive shift: g²/δ.
#### `lambda_i(g_i, delta_i)` — Coupling parameter: -g/δ.
#### `gl_second(lambda_i, lambda_i1, delta_i, delta_i1)` — Second-order Kerr correction.
#### `K0(chi_0, chi_1, lambda0, lambda1, gl0)` — Zeroth-order Kerr coefficient.
#### `K1(chi_0, chi_1, lambda0, lambda1)` — First-order Kerr coefficient.
#### `zeta(K_0, K_1)` — Cross-Kerr from Kerr coefficients: (K1-K0)/2.
#### `zeta_pr(K_0, K_1)` — Dressed cross-Kerr: (K1+K0)/2.
#### `zeta_suri(...)` / `zeta_pr_suri(...)` — Suri's formulas for cross-Kerr.
#### `fr_shift(n, fr, chi, zeta, zeta_pr)` — Resonator frequency shift at photon number n.

### TLS Resonator Models

#### `df_TLS(T, freq, delta)` — TLS frequency shift vs. temperature (digamma function model).
#### `QTLS(T, freq, delta)` — TLS quality factor: δ × tanh(hf/2kT).
#### `QTLS_corr(T, freq, delta, A)` — Corrected TLS Q-factor with phenomenological parameter A.
#### `QTSL_pow(n_av, n_c, beta, Delta)` — Power-dependent TLS loss: Δ/√(1 + (n/nc)^β).

### Unit Conversions

#### `dBm_to_W(PdBm)` — dBm → Watts.
#### `n_from_Q(P, Ql, Qc, f)` — Average photon number from power and Q-factors.
#### `from_dB_to_lin(mag)` — dB magnitude to linear.
#### `power_to_rate(P_W, Ampl, w, gamma)` — Drive power to Rabi rate.
#### `kappa(fr, Ql)` — Resonator linewidth.
#### `n_crit(delta, g)` — Critical photon number: δ²/4g².
#### `EJ(R, T)` — Josephson energy from junction resistance R at temperature T.
#### `n_T(T, w)` — Thermal photon occupation at temperature T and frequency w.

### Impedance Models

#### `Z_serial(w, wr, R, C)` — Serial RLC impedance.
#### `Z_rCR(w, wr, R, C_q, C_r, Z0)` — Transmission line + lumped element impedance.
#### `Z_tan(w, wr, R, C_q, C_r, Z0)` — Tangent-model impedance.
#### `Qc(Z0, R0, Cc, f)` — Coupling quality factor from coupling capacitance.

### Analytical Spectroscopy Model

#### `n_plus(eps, kappa, chi, delta)` / `n_minus(...)` — Photon populations for driven resonator.
#### `D_s(n_p, n_m, kappa, chi, delta)` — Effective decoherence parameter.
#### `Gamma_m(Ds, kappa)` — Measurement-induced dephasing rate.
#### `A_coeff(Ds, kappa, chi, delta)` / `B_coeff(Ds, n_p, n_m, chi)` — Spectroscopy model coefficients.
#### `S(f, f0, chi, delta, eps, kappa, gamma0, alpha)` — Full spectroscopy lineshape function (sum of 20 sidebands).

### File Utilities

#### `findpath(database, dataname)` — Walks directory tree to find a file.
#### `find_files(folder_name)` — Lists `.mat` files sorted by numeric label. Returns `(names, temps)`.
#### `loadmatfile(path)` — Loads a `.mat` file.

### Plotting

#### `plot_2d(X, Y, Z, flip=False, cmap='Reds')` — 2D color plot (imshow). Returns `cax`.
#### `plot_with_errors(X, Y, ERR, label='data', alpha=0.2)` — Line plot with shaded error band.
#### `shift_flux(fr, flux)` — Estimates flux periodicity and zero-crossing from frequency-vs-flux data. Returns `(zero_flux, period)`.

### Class `Qfactor`
Automated resonator Q-factor extraction from S-parameter data.

- **`__init__(file_name, Att=-74)`** — Loads `.mat` file; `Att` is total attenuation in dB.
- **`corr_base_level()`** — Corrects baseline slope in magnitude data.
- **`calc(N)`** — Fits resonances in a window of ±N points. Populates `fr, Ql, Qc, Qi, n_av` and their errors.
- **`plot_Q()`** — Plots Ql, Qc, Qi with error bands.
- **`plot_f()`** — Plots resonator frequency.
- **`plot_data()`** — 2D heatmap of raw magnitude data.
- **`save_data(name)`** — Saves extracted Q-factors to text file.

### Class `Resonator_T_P`
Temperature- and power-dependent resonator analysis.

- **`__init__(file_name_list, Temp, Att=-75)`** — Loads multiple datasets at different temperatures.
- **`fit_data(corr='no', N=500)`** — Fits all datasets.
- **`make_data_array()`** — Assembles results into 2D arrays indexed by (temperature, power).
- **`fit_fTdep()`** — Fits frequency vs. temperature using TLS model.
- **`fit_QTdep(func='corr', p0, bounds)`** — Fits Q vs. temperature.
- **`fit_QPdep(beta=1)`** — Fits Q vs. photon number (power dependence).
