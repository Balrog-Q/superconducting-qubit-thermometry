# Superconducting Qubit Thermometry

Experimental control and data-analysis code for **thermometry based on a superconducting transmon qubit**.
The project uses a Zurich Instruments SHFQC and the LabOne Q SDK to run calibration sequences, qubit characterisation experiments, and three-level population measurements that extract the effective temperature of the qubit's electromagnetic environment.

## Overview

The core idea is to treat a transmon qubit as a primary thermometer: by measuring the steady-state populations of its ground (|g⟩), first-excited (|e⟩), and second-excited (|f⟩) states, one can infer the effective temperature of the qubit's thermal bath using the Boltzmann distribution. Additional experiments probe the qubit via SINIS (Superconductor–Insulator–Normal metal–Insulator–Superconductor) junction thermometry for cross-calibration.

The main deliverables are:

- **`lib/`** — a reusable Python library for instrument control, experiment construction, curve fitting, and temperature extraction.
- **`qmeas/`** — a lightweight package for sample/parameter bookkeeping (on-disk layout, named parameter sets, JSON save/load).
- **`scresonators_custom.py`** — a dependency-free resonator (single-tone spectroscopy) fitting module used to extract `f0`, `Qi`, and `Qc`.
- **`S3_Q2_Cooldown_2.ipynb`** — a Jupyter notebook that walks through an entire cooldown measurement campaign (sample S3, qubit Q2, cooldown #2). `S3_Q2_Cooldown_2_update.ipynb` is a trimmed, updated variant of the same campaign.
- **`slicing_code/`** — the same workflow split into smaller, topic-focused notebooks (imports, spectroscopy, control-pulse setup, readout optimisation, single-shot).
- **`Q1_Qi_Fits_Nb.ipynb`** — a standalone notebook for internal quality-factor (`Qi`) fitting of resonators on sample qubit Q1.

## Project Structure

```
superconducting-qubit-thermometry/
├── S3_Q2_Cooldown_2.ipynb          # Main experiment notebook
├── S3_Q2_Cooldown_2_update.ipynb   # Trimmed / updated variant of the main notebook
├── Q1_Qi_Fits_Nb.ipynb             # Resonator internal-Q (Qi) fitting notebook
├── scresonators_custom.py          # Standalone single-tone-spectroscopy resonator fit
├── lib/
│   ├── devices/                    # Instrument driver wrappers (VISA / HTTP)
│   │   ├── KeysightDMM34465A.py    #   Keysight 34465A digital multimeter
│   │   ├── KeysightWG33622A.py     #   Keysight 33622A waveform generator
│   │   ├── SIM_wrapper.py          #   SRS SIM900 / SIM928 voltage source
│   │   ├── YokoGS200_wrapper.py    #   Yokogawa GS200 voltage/current source
│   │   ├── XLD_Server_Client.py    #   BlueFors XLD dilution fridge HTTP client
│   │   ├── XLD_Server_Passkey.py   #   Credentials for the XLD server (git-ignored)
│   │   └── bftc_credentials.py     #   BlueFors temperature controller credentials (git-ignored)
│   ├── helpers/                    # Experiment builders, fitting, & analysis
│   │   ├── setup_helper.py         #   SHFQC descriptor & calibration definition
│   │   ├── descriptor_*.yml        #   LabOne Q device-setup descriptors (SHFQC, HDAWG, ...)
│   │   ├── meas_helper.py          #   Experiment pulse sequences (original)
│   │   ├── meas_helper_mod.py      #   Experiment pulse sequences (extended)
│   │   ├── meas_helper_mod_2.py    #   Additional experiment variants
│   │   ├── create_meas_helper.py   #   High-level "create_*" wrappers
│   │   ├── fitting_helper.py       #   Curve fitting & data processing
│   │   ├── pop_temp_helper.py      #   Population → temperature (two-level)
│   │   ├── pop_temp_helper_v2.py   #   Population → temperature (three-level)
│   │   ├── save_data_helper.py     #   Data persistence utilities
│   │   ├── feedback_helper.py      #   Feedback / active-reset helpers
│   │   ├── randomized_benchmarking_helper.py
│   │   ├── example_notebook_helper.py
│   │   └── example_notebook_simple.py
│   ├── utils/
│   │   ├── calculator.py           #   Physics calculators (dispersive shift, TLS loss, Q-factor analysis)
│   │   └── ding.mp3                #   Audio notification for long measurements
│   └── Per-module documentation for lib_.md
├── qmeas/                          # Sample & parameter management package
│   ├── qsample.py                  #   QSample: on-disk sample/structure layout
│   └── qparameters.py              #   QBaseParameters / QLinkedParameters
├── scresonators/                   # Vendored upstream scresonators-fit package
├── slicing_code/                   # Modular notebook breakdown (git-ignored)
│   ├── 1-imports_&_init.ipynb
│   ├── 2-spectroscopy.ipynb
│   ├── 3-control_pulse_setup.ipynb
│   ├── 4_readout_optimization.ipynb
│   └── 5-single_shot_0_&_1_measurements.ipynb
├── BlueFTC/                        # Third-party BlueFors temp-controller driver (git-ignored)
├── requirements.txt
├── QUICKSTART.md
└── docs/                           # Reference PDFs (not tracked in git)
    ├── 2025 - Thermometry Based on a Superconducting Qubit.pdf
    ├── Thesis - Thermometry based on a superconducting qubit.pdf
    ├── Thesis - Techniques and protocols for temperature sensing with a transmon qubit.pdf
    ├── 2019 - Introduction to Experimental Quantum Measurement.pdf
    └── 2019 - Quantum Engineer's Guide to Superconducting Qubits.pdf
```

## Library Reference

### `lib/devices/` — Instrument Drivers

All drivers communicate via **PyVISA** (GPIB/TCP) or HTTP and follow a common `open_inst` / `close_inst` pattern.

| Module | Instrument | Purpose |
|---|---|---|
| `YokoGS200_wrapper.py` | Yokogawa GS200 | DC voltage/current source for flux biasing |
| `SIM_wrapper.py` | SRS SIM900 + SIM928 | Multi-channel DC voltage source |
| `KeysightDMM34465A.py` | Keysight 34465A | Digital multimeter for SINIS IV readout |
| `KeysightWG33622A.py` | Keysight 33622A | Waveform generator |
| `XLD_Server_Client.py` | BlueFors XLD | HTTP client for dilution fridge temperature sweep coordination |

### `lib/helpers/` — Experiment Construction & Analysis

#### `setup_helper.py`
Defines the SHFQC hardware descriptor (device address `DEV12192`) and the `define_calibration()` function that maps qubit/readout parameters to LabOne Q `SignalCalibration` objects. Signal lines:
- `q0/drive_line` — qubit g↔e drive
- `q0/drive_ef_line` — qubit e↔f drive
- `q0/th_res_line` — thermal resonator / fast flux line
- `q0/measure_line` + `q0/acquire_line` — dispersive readout

#### `meas_helper_mod.py`
The main experiment factory. Key functions:
- **Calibration builders**: `readout_calib()`, `res_spec_calib()`, `qubit_spec_calib()`, `make_ramsey_calib()`, `make_th_res_calib()`, etc.
- **Signal maps**: `MA_map`, `qubit_meas_map`, `qubit_ef_map`, `qubit_all_map`, etc.
- **Experiment builders**: `make_rabi()`, `make_t1()`, `make_ramsey()`, `make_echo()`, `make_rabi_ef_1/2()`, `make_T1_ef_1()`, `make_ramsey_ef_2()`
- **Population experiments**: `make_exp_population_full()`, `make_exp_population_flux()`, `make_exp_pop_correlations()`
- **RPM (Rabi Population Measurement)**: `get_rabi_population_calibration_measurement()`, `get_quick_rabi_population_measurement()`
- **Spectroscopy**: `res_spectroscopy()`, `qubit_spectroscopy()`, `qubit_ef_spectroscopy()`

#### `create_meas_helper.py`
Thin convenience layer that calls `meas_helper_mod` builders, then auto-applies calibration and signal maps. Functions like `create_rabi()`, `create_t1()`, `create_ramsey()`, `create_exp_population_full()`, etc.

#### `fitting_helper.py`
Curve-fitting routines and data utilities:
- **Models**: Lorentzian, Fano, exponential decay, decaying oscillation, Gaussian, bimodal Gaussian, linear, parabolic
- **Fit wrappers**: `fit_Rabi()`, `fit_Ramsey()`, `fit_T1()`, `fit_T1_ef()`, `fit_Spec()`, `fit_ResSpec()`
- **Auto-fit**: `auto_T1_fit()`, `auto_ramsey_fit()`, `auto_echo_fit()` — automatically estimate initial parameters via FFT
- **PCA**: `compute_pca()` for IQ-plane rotation
- **Data transforms**: `rotate_and_norm()`, `transform_complex_to_real()`, `average_by_N()`, `reshape_to_1D/2D()`

#### `pop_temp_helper.py` / `pop_temp_helper_v2.py`
Temperature extraction from three-level population data:
- `get_ABC()` — compute the 9 A, B, C population ratios from six readout points (x0–x2, y0–y2)
- `make_projection()` — rotate complex IQ data to real/imaginary axes
- `get_temperature()` — convert ABC ratios to effective temperatures (v2 supports full three-level model via `scipy.optimize.fsolve`)
- `make_all_temperatures()`, `make_optimal_temperature()`, `find_optimal_temperature()` — pipeline for extracting optimised temperature estimates
- `get_ABC_parallel()` — alternative "parallel" data processing approach

#### `calculator.py`
Physics utility functions:
- Transmon parameters: `n_10()` (matrix elements), `chi()` (dispersive shift), Kerr coefficients
- TLS resonator models: `df_TLS()`, `QTLS()`, `QTLS_corr()`
- `Qfactor` class — automated resonator quality-factor extraction from S-parameter data
- `Resonator_T_P` class — temperature- and power-dependent Q-factor analysis

### `lib/utils/`
- `calculator.py` (see above)
- `ding.mp3` — audio notification played when a long measurement finishes

### `qmeas/` — Sample & Parameter Management
Lightweight helpers that the notebooks use to organise measured data and parameters:
- `QSample` (`qsample.py`) — describes where a sample/structure lives on disk. Parameter files live under `<directory>/<sample>/<structure>/parameters`.
- `QBaseParameters` (`qparameters.py`) — a `dict` subclass holding a named parameter set (qubit parameters, LO settings, ...) bound to a `QSample`, with `update_parameter()`/`add_parameter()`/`get_parameter()` helpers and JSON `save()`/`load()`.
- `QLinkedParameters` — extends `QBaseParameters` with fallback resolution against one or more linked parameter sets, so a per-experiment set can inherit from a shared base without copying values.

### `scresonators_custom.py` — Single-Tone Spectroscopy Fitting
A self-contained (numpy/scipy/matplotlib only) replacement for the external `scresonators` wrapper used by the spectroscopy notebooks. It fits a complex S21 trace to the asymmetric-Lorentzian / Diameter-Correction-Method (DCM) model for a notch (hanger) resonator:
- `fit_single_STS_wrapper(freqs, y_data)` → `(full_result, quick_result, sweep_manager)`; `quick_result` is a compact dict `{f0, qc, qi, ...}` used to update `qubit_parameters['ro_freq']`.
- `plot_single_STS_wrapper(sweep_man=...)` — plots the raw data and fitted curve.
- `SweepManager` — container holding the raw trace, sweep metadata, and fit results.

### `scresonators/`
A vendored copy of the upstream [`scresonators-fit`](https://github.com/boulder-cryogenic-quantum-testbed/scresonators) package (MIT), which fits complex S21 data for hanger-mode resonators using DCM, INV, CPZM, and PHI methods. Used by `Q1_Qi_Fits_Nb.ipynb` for internal-Q analysis.

## Notebook Workflow (`S3_Q2_Cooldown_2.ipynb`)

The notebook is organised into the following major sections:

1. **Imports & Initialisation** — load libraries, connect to the SHFQC, configure the Yokogawa flux source, set sample/qubit parameters.
2. **Spectroscopy** — pulsed resonator and qubit spectroscopy (g↔e and e↔f transitions), including flux-dependent spectroscopy.
3. **Control Pulse Setup**
   - *First transition (g↔e)*: amplitude Rabi, T1, Ramsey, Hahn echo, Rabi error amplification → calibrate π and π/2 pulses.
   - *Second transition (e↔f)*: same characterisation suite for the e↔f drive.
4. **Readout Optimisation** — resonator spectroscopy in |g⟩, |e⟩, |f⟩ states; single-shot discrimination; readout pulse/integration tuning.
5. **Population Measurements**
   - Rabi Population Measurement (RPM) calibration.
   - Three-level population measurement (6-point sequence: x0–x2, y0–y2) → ABC ratios → effective temperature.
   - Statistical analysis, IQ rotation optimisation, prepulse variants.
6. **Fast Flux Drive** — flux pulse calibration, decay vs. detuning, population measurement with flux excitation.
7. **SINIS Calibration & Temperature Sweeps** — DC IV-curve measurement of SINIS junctions for cross-calibrated thermometry; flux sweeps; local heating experiments; dilution-fridge temperature sweeps.

The same phases are also available as smaller, standalone notebooks under `slicing_code/` (imports/init, spectroscopy, control-pulse setup, readout optimisation, single-shot measurements), which are easier to run and debug in isolation.

## Hardware Requirements

This code is designed to run on a measurement PC connected to:

- **Zurich Instruments SHFQC** (address `DEV12192`) — qubit control & readout
- **Yokogawa GS200** — DC flux bias
- **SRS SIM900 mainframe + SIM928 modules** — additional DC voltage sources
- **Keysight 34465A DMM** — SINIS junction voltage readout
- **Keysight 33622A** — waveform generator for SINIS biasing
- **BlueFors XLD dilution refrigerator** — cryogenic cooling (HTTP API for temperature readout and sweep coordination)

## References

The following reference materials are included in the project directory:

- *Thermometry Based on a Superconducting Qubit* (2025)
- *Techniques and protocols for temperature sensing with a transmon qubit* (Thesis)
- *Thermometry based on a superconducting qubit* (Thesis)
- *Introduction to Experimental Quantum Measurement* (2019)
- *Quantum Engineer's Guide to Superconducting Qubits* (2019)
