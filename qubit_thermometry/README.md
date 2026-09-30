# qubit_thermometry

**Version: v2.0.0**

`qubit_thermometry` is a LabOne Q / LabOne Q Applications based toolkit for tuning up a
single superconducting qubit and running effective-temperature (thermometry) measurements
on it: population/temperature analysis, fast-flux-drive experiments, and SINIS-based DC
calibration and heating sweeps.

It is a restructured, modular successor to the single monolithic `Workflow-v1.7.3.json`
notebook (625 cells, ~9000 lines) that used to contain every experiment. That notebook has
been split into **4 focused template notebooks**, backed by a shared, reusable Python
package (`src/qubit_thermometry`) modeled on the `experiments/` + `analysis/` layout of
[`laboneq_applications`](../laboneq-applications).

## Why this structure

The original notebook mixed generic setup, 12 tune-up experiments, single-shot/population
measurements, fast-flux experiments, and SINIS DC-calibration/heating sweeps in one place,
with a lot of near-duplicated code (e.g. the same manual sweep loop written out twice for
the g-e and e-f transitions, or ~8 nearly identical "heating sweep" subsections in the SINIS
section). Splitting the work this way:

- Lets you run/re-run only the part of the workflow you need (e.g. re-run just the SINIS
  heating sweeps without re-doing the full tune-up).
- Moves all reusable logic (fitting, temperature calculations, plotting, custom LabOne Q
  experiments) out of notebook cells and into a tested, importable package, so notebook
  cells stay short: *set parameters -> run a workflow -> analyze/plot*.
- Only the tune-up notebook builds and saves the QPU (qubits + calibrated parameters) from
  scratch; the other three notebooks load that saved QPU and connect to the instruments
  needed for their own measurements.

## The 4 template notebooks

All notebooks live in `templates/` and are meant to be copied/renamed per cooldown and
filled in with real hardware values (device IDs, sample name, etc.) before running.

Run them in this order:

1. **`tune-up_experiments_workflow.ipynb`** - Tune-up experiments.
   Builds the `DeviceSetup` and a brand-new QPU from manually-entered starting parameters,
   then runs: Resonator & Qubit Spectroscopy; Amplitude Rabi, Amplitude Rabi Chevron, Rabi
   Chevron, Rabi Frequency Calibration, T1 Lifetime, Ramsey, Rabi Error Amplification, DRAG
   Calibration and Hahn-Echo (each for both the g-e and e-f transitions); and Readout
   Amplitude Optimisation + Dispersive Shift. Every experiment that changes a QPU parameter
   saves the QPU immediately and appends a short entry to an in-notebook `tuning_log`. The
   **final cell** prints a full summary: every qubit's final tuned parameters, the ordered
   list of what was tuned, and the file path the QPU was saved to.

2. **`population_&_temperature_measurements_workflow.ipynb`** - Population & temperature
   measurements. Loads the tuned QPU, then runs: Single Shot 0 & 1 Measurements (one
   measurement plus 3 sweeps - vs. Rabi/drive-length, vs. integration length & delay, vs.
   readout amplitude & length - each picking the sweep point with the highest g/e/f
   assignment fidelity); and Population Measurements (Rabi Population Measurement setup,
   oscillation/pi-pulse checks, population + effective-temperature measurement, three-level
   population statistics, projection-phase/rotation optimization, population with a swept
   ge pre-pulse, and population vs. readout frequency). Readout-tuning steps here still
   update and re-save the QPU, matching the original notebook's behavior.

3. **`fast_flux_drive_workflow.ipynb`** - Fast Flux Drive. Loads the tuned QPU and runs
   flux-pulse-only experiments on the qubit's own flux/`th_res` line: flux-amplitude
   calibration, a flux-pulse timing check, T1 decay under flux detuning, population with a
   flux drive (single point + sweep), and T1 + population vs. flux amplitude simultaneously.
   This notebook is purely diagnostic - it never updates or re-saves the QPU.

4. **`sinis_calibration_&_temperature_sweep_workflow.ipynb`** - SINIS Calibration,
   Statistics and Temperature Sweep Measurements. Loads the tuned QPU, connects the DC
   instruments (BlueFors temperature controller, Keysight DMM, SIM928 heater-bias sources),
   runs a qubit-health "Statistics" loop, then runs ~8 heating-bias sweeps (nonlocal/local
   heating, several bias ranges and split-junction geometries, with and without
   single-shot-readout data collection) that read the SINIS thermometer voltage and the
   qubit's population/T1/Ramsey response at each bias point.

### Every loop-based sweep suppresses per-iteration logging

Any cell (or helper function) that runs a LabOne Q workflow repeatedly inside a `for`/`while`
loop wraps that loop in `qubit_thermometry.helper.setup.logging_disabled(folder_store,
logging_store)`. This deactivates LabOne Q's `FolderStore`/`LoggingStore` logbooks for the
duration of the sweep, so only the sweep's own aggregated `.mat`/`.png` outputs are saved,
instead of one full logbook entry per sweep point. One-shot (non-looped) experiment cells
are unaffected and keep logging active.

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

After that, fill in the `# TODO` cells for your setup: `shfqc_device_id`/`ip_address`
(device descriptor), and `sample_name`/`qubit_name`/`cooldown_start_date` (used to locate
the per-cooldown data directory and the QPU file shared across all 4 notebooks). The
tune-up notebook additionally needs the starting per-qubit calibration guesses (drive/readout
frequencies, ranges, etc.) filled in near its device-setup cells.

If you prefer an installed package over the `sys.path` bootstrap, `qubit_thermometry` also
has its own `pyproject.toml`:

```sh
pip install -e qubit_thermometry/
```

## Known items carried over from the original notebook

A couple of pre-existing inconsistencies in `Workflow-v1.7.3.json` were intentionally
preserved (not silently fixed) during the port, and are flagged with `NOTE` comments in
`tune-up_experiments_workflow.ipynb`, since fixing them would change tuning behavior:

- "Amplitude Rabi Chevron" always computes its sweep frequencies from
  `resonance_frequency_ge`, even when run for the e-f transition.
- "DRAG Calibration": the g-e "Run Workflow" cell does not pass `temporary_parameters` to
  `drag_q_scaling.experiment_workflow`, while the e-f mirror does.

Review these and decide whether to fix them for your setup.
