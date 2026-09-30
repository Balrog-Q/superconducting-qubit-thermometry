# qubit_thermometry

**Version**: <b><font color="#008000">v2.0.0</font></b>

## Changelog

All changes must be logged here! Do not make changes to this notebook other than expanding or modifying the standard experiments in a meaningful! All device-specific parameters and measurements have to be done in a different notebook!

Stick to semantic versioning:
- **Last Digit**: Fix a bug that does not add any new features and is backwards compatible -> increment last digit by one (e.g. 0.0.4 to 0.0.5)
- **Middle Digit**: Add a new feature while keeping backwards compatibility (older versions can still be executed without any modifications) -> increment middle digit by one and set last digit to 0 (e.g. 1.2.12 to 1.3.0)
- **First Digit**: Make changes that will break older versions, making them incompatible with the new version -> increment first digit by one and set all other digits to 0 (e.g. 3.2.9 to 4.0.0)

**Logging Book:** 
1. Version v1.0.0 (up to version v1.7.4)
	- **2026-07-23**, *Elias*: Created this template notebook and added resonator and qubit spectroscopy, amplitude Rabi, Ramsey T1 and DRAG. (v1.0.0)
	- **2026-08-07**, *Kha*: Updated Hahn Echo, added Readout Optimisation, Single Shots, Population Measurements. (v1.2.0)
	- **2026-08-13**, *Kha*: Added Rabi Shevron, Rabi Frequency Calibration, Rabi Error Amplification. (v1.4.0)
	- **2026-08-26**, *Kha*: Update code output, visualization, and Amplitude Rabi Chevron. (v1.5.5)
	- **2026-08-27**, *Kha*: New experiments: Fast Flux Drive, SINIS Calibration. (v1.7.0)
	- **2026-08-27**, *Kha*: Fix table of content bug. (v1.7.1)
	- **2026-09-02**, *Kha*: Fix logging data bug, order of experiments (T1 Lifetime -> Ramsey -> Rabi Error Amplification). (v1.7.2)
	- **2026-09-26**, *Kha*: Change the Single shot measurement with different rabi freq, integration lengths and delays, readout amplitudes and lengths, using the fidelity as the optimal points. (v1.7.3)
	- **2026-09-26**, *Kha*: Every loop-based sweep suppresses per-iteration logging. Any cell (or helper function) that runs a LabOne Q workflow repeatedly inside a `for`/`while` loop wraps that loop in `qubit_thermometry.helper.setup.logging_disabled(folder_store, logging_store)`. This deactivates LabOne Q's `FolderStore`/`LoggingStore` logbooks for the duration of the sweep, so only the sweep's own aggregated `.mat`/`.png` outputs are saved, instead of one full logbook entry per sweep point. One-shot (non-looped) experiment cells are unaffected and keep logging active. (v1.7.4)
2. Version v2.0.0
	- **2026-09-27**, *Kha*: Separate all 4 section from previous version v1.7.4 into 4 distinct experiments script: Tune-up experiments, Population & temperature experiments, Flux drive experiments, and SINIS calibration & temperature sweep experiments. (v2.0.0)

## Package layout (`src/qubit_thermometry`)

```
src/qubit_thermometry/
  helper/            # Shared, dependency-light functions used by every notebook
  workflow/
    experiments/     # Custom LabOne Q experiments not provided by laboneq_applications
    analysis/        # Fitting/plotting called after a workflow runs
```

### `helper/` - organized by functionality, not by which notebook first needed it

- **`setup.py`** - `DeviceSetup`/session/data-directory bootstrap: `build_device_setup`,
  `connect_session`, `init_data_saving`, `setup_logbook`, `logging_disabled`, plus small
  generic utilities `set_transition`, `log_sweep_help`, `get_path_to_file`,
  `get_analysis_task_output`.
- **`qpu_io.py`** - `save_qpu`, `load_qpu`, `print_qpu_summary` (used by the tune-up
  notebook's final cell).
- **`data_io.py`** - `build_mat_payload`/`save_mat` (replace the `attrs.asdict(...)` +
  `savemat(...)` boilerplate every "Update Parameters" cell used to repeat) and
  `update_shots_mat` (incremental single-shot `.mat` accumulation for SINIS SSRO sweeps).
- **`fitting.py`** - oscillation/exponential/linear curve-fitting helpers (`fit_rabi_osc`,
  `auto_T1_fit`, `fit_T1`, `rotate_and_norm`, etc.), used by Population and Fast Flux Drive.
- **`temperature.py`** - population -> `pe/pg` -> effective-temperature calculations
  (`get_ABC`/`get_ABC_parallel`, `get_temperature`, `collect_population_from_result`, ...),
  used by Population, Fast Flux Drive and SINIS Calibration.
- **`plotting.py`** - shared temperature/statistics/2D plotting (`plot_temp_single`,
  `plot_stat`, `plot_rotation_stat`, `plot_2d`).
- **`single_shot.py`** - IQ-blob single-shot analysis (`analyze_single_shots`,
  `collect_shots_from_result`, `summarize_single_shot_metrics`).
- **`sinis_devices.py`** - DC-instrument connection helpers specific to SINIS Calibration
  (`connect_temperature_controller`, `connect_dc_voltmeter`, `connect_sim_voltage_source`,
  `ramp_voltage_with_retry`); the only `helper/` module that depends on the repo-root `lib/`
  hardware drivers.

### `workflow/experiments/` - custom experiment/workflow pairs

Each module follows the `create_*_experiment` (`@workflow.task`) +
`*_experiment_workflow` (`@workflow.workflow`) pattern used throughout
`laboneq_applications.experiments`, for experiments that `laboneq_applications` does not
already provide:

- `rabi_chevron.py`, `rabi_frequency_calibration.py` - generalize the tune-up notebook's
  manual detuning/drive-length sweeps (previously duplicated once per transition) into one
  function each, parametrized by `transition`.
- `population.py`, `rabi_population.py`, `quick_rabi_population.py` - the three-level
  population protocol and the Rabi Population Measurement (RPM) experiments.
- `flux_amplitude_calibration.py`, `fast_flux_decay.py`, `population_flux.py` - the Fast
  Flux Drive experiments.
- `sinis_heating_sweep.py` - `run_heating_sweep` (generalizes all ~8 SINIS heating-sweep
  subsections into one parametrized function) and `run_qubit_health_statistics` (the
  no-bias-ramp "Statistics" loop).

### `workflow/analysis/` - fitting/plotting called after a workflow runs

One module per experiment (`dispersive_shift.py`, `rabi_chevron.py`,
`rabi_frequency_calibration.py`, `single_shot.py`, `population.py`, `rabi_population.py`,
`fast_flux.py`, `sinis_heating.py`), matching `workflow/experiments/`, following the
`analysis/*.py` convention of `laboneq_applications`.

## Running a template notebook

Every notebook's first cell adds the package to `sys.path` so no install step is required:

```python
import sys
from pathlib import Path

REPO_ROOT = Path("/path/to/qubit-thermometry_v2.0")
sys.path.insert(0, str(REPO_ROOT / "qubit_thermometry" / "src"))
```

The SINIS notebook additionally adds `REPO_ROOT` itself to `sys.path`, since
`helper/sinis_devices.py` imports the hardware drivers under the repo-root `lib/` package.

After that, fill in the `# TODO` cells for your setup: `shfqc_device_id/ip_address` (device descriptor), and `sample_name/qubit_name/cooldown_start_date` (used to locate the per-cooldown data directory and the QPU file shared across all 4 notebooks). The tune-up notebook additionally needs the starting per-qubit calibration guesses (drive/readout frequencies, ranges, etc.) filled in near its device-setup cells.

If you prefer an installed package over the `sys.path` bootstrap, `qubit_thermometry` also has its own `pyproject.toml`:

```sh
pip install -e qubit_thermometry/
```
