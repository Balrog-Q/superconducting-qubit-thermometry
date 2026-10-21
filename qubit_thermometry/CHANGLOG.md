# `qubit_thermometry` version `v2.0.0`

> Release data: 2026-09-27 $\cdot$ Author: Kha

### Breaking release.
The monolithic `Workflow-v1.7.3` notebook (625 cells, ~9000 lines) has been split into four focused template notebooks backed by a reusable Python package. Workflows written against `v1.7.x` will not run unchanged.

### Highlights
- **Four separate experiment scripts** replace the single all-in-one notebook:
1. `tune-up_experiments_workflow.ipynb` — device setup, QPU creation, spectroscopy, Rabi/Chevron/frequency calibration, T1, Ramsey, error amplification, DRAG, Hahn echo (g-e and e-f), readout amplitude optimisation and dispersive shift. Saves the QPU after every parameter-changing step, maintains a tuning_log, and prints a final tuned-parameter summary.
2. `population_&_temperature_measurements_workflow.ipynb` — single-shot 0/1 measurements plus three fidelity-optimised sweeps, and the full population / effective-temperature suite.
3. `fast_flux_drive_workflow.ipynb` — flux-amplitude calibration, pulse-timing check, T1 under flux detuning, population with flux drive. Purely diagnostic; never re-saves the QPU.
4. `sinis_calibration_&_temperature_sweep_workflow.ipynb` — DC instrument connection (BlueFors controller, Keysight DMM, SIM928 sources), qubit-health statistics loop, and the heating-bias sweeps.
- New qubit_thermometry package (`qubit_thermometry/src/qubit_thermometry`) modeled on the `laboneq_applications` layout:
	- `helper/` — setup/session bootstrap, QPU I/O, .mat data I/O, fitting, temperature calculations, plotting, single-shot IQ analysis, and SINIS DC-device helpers.
	- `workflow/experiments/` — custom `create_*_experiment / *_experiment_workflow` pairs for experiments not provided by `laboneq_applications`.
	- `workflow/analysis/` — one analysis module per experiment.
- **Deduplicated sweep logic.** Per-transition Rabi Chevron / frequency-calibration sweeps are now single functions parametrized by transition, and the ~8 near-identical SINIS heating-sweep sections collapse into one run_heating_sweep.
- **Shared QPU across notebooks.** Only the tune-up notebook builds and saves the QPU; the other three load it and connect only the instruments they need.
- **Reduced logbook noise.** Loop-based sweeps wrap in `helper.setup.logging_disabled(...)`, so only aggregated .mat/.png outputs are written instead of one logbook entry per sweep point (carried in from `v1.7.4`).
- **Installable.** `pip install -e qubit_thermometry/`, or use the `sys.path` bootstrap in each notebook's first cell.
- **Documentation.** New top-level `README.md` covering rationale, notebook order, package layout, and setup; `qubit_thermometry/README.md` now focuses on the changelog and package reference.
- `laboneq-applications` added as a git submodule for reference alongside the new layout.

### Upgrade notes
•  Copy/rename the templates/ notebooks per cooldown and fill in the # TODO cells: `shfqc_device_id` / `ip_address`, `sample_name`, `qubit_name`, `cooldown_start_date`, plus the starting per-qubit calibration guesses in the tune-up notebook.
•  Run the notebooks in the order listed above — the last three require the QPU saved by the tune-up notebook.
•  The SINIS notebook must also add the repo root to `sys.path`, since `helper/sinis_devices.py` imports the drivers under `lib/`.