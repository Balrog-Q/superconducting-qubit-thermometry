"""Device/session setup, data-saving bootstrap and generic sweep helpers.

These functions replace the "Package Imports and Initialization" section that
used to be duplicated at the top of every experiment notebook
(``Workflow-v1.7.3.json`` cells 15-30). Every template notebook calls into
this module to build its ``DeviceSetup``/qubits (tune-up) or to reconnect a
``Session`` and data-saving directories (the other three notebooks, after
loading the tuned QPU with :mod:`qubit_thermometry.helper.qpu_io`).
"""

from __future__ import annotations

import os
import time
from contextlib import contextmanager

import numpy as np
from laboneq.contrib.example_helpers.generate_descriptor import generate_descriptor
from laboneq.simple import DeviceSetup, Session, workflow
from laboneq.workflow.logbook import LoggingStore
from laboneq_applications.qpu_types.tunable_transmon import TunableTransmonQubit

DEFAULT_DATA_ROOT = os.path.join("N:\\", "xld", "qubit_thermometry_v2")


def set_transition(transition: str) -> str:
    """Validate and return a `ge`/`ef` transition label."""
    assert transition in ("ge", "ef"), "Choose transition from 'ge' or 'ef'!"
    return transition


def log_sweep_help(t1_min: float, t1_max: float, t1_num: int) -> np.ndarray:
    """Log-spaced sweep array starting at 0, useful for T1/decay delays."""
    t1_log_sweep = np.logspace(np.log10(t1_max / t1_num / 10), np.log10(t1_max), t1_num - 1)
    return np.append([0.0], t1_log_sweep)


def get_path_to_file(file_name: str, extension: str, directory: str) -> str:
    """Timestamped file path inside the given data directory.

    Bind ``directory`` once a notebook has computed its
    ``data_root_directory``, e.g.::

        from functools import partial
        get_path_to_file = partial(setup.get_path_to_file, directory=data_root_directory)
    """
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    return os.path.join(directory, f"{timestamp}_{file_name}{extension}")


def get_analysis_task_output(workflow_result, task_name: str):
    """Output of a task inside the nested `analysis_workflow` of a workflow result.

    Used to reach outputs that are not part of the analysis-workflow's own
    output, e.g. `fit_data` or `calculate_signal_differences`.
    """
    return workflow_result.tasks["analysis_workflow"].tasks[task_name].output


def build_device_setup(
    *,
    shfqc_device_id: str,
    number_of_qubits: int = 1,
    ip_address: str = "localhost",
    device_options: str = "SHFQC/QC2CH",
    multiplex: bool = True,
    include_cr_lines: bool = False,
):
    """Build the `DeviceSetup` and the list of `TunableTransmonQubit`s.

    `DeviceSetup` describes the physical instrument connections (ports,
    instrument IPs, ...) and is not part of the saved/loaded QPU, so **every**
    template notebook calls this to (re)build it and connect a `Session`
    (see `connect_session`) with the same descriptor arguments (device IDs,
    IP address, ...), even the three that then load a previously tuned QPU
    with `qpu_io.load_qpu` instead of using the qubits returned here.

    Only the tune-up notebook uses the *qubits* returned by this function
    (to build a brand-new QPU); the other three notebooks discard them and
    use `qpu.quantum_elements` from the loaded QPU instead, since those
    carry the actual tuned parameters.
    """
    descriptor = generate_descriptor(
        shfqc_2=[shfqc_device_id],
        number_data_qubits=number_of_qubits,
        multiplex=multiplex,
        number_multiplex=number_of_qubits,
        include_cr_lines=include_cr_lines,
        ip_address=ip_address,
    )
    device_setup = DeviceSetup.from_descriptor(descriptor, ip_address)
    device_setup.instruments[0].device_options = device_options
    qubits = TunableTransmonQubit.from_device_setup(device_setup)
    return device_setup, qubits


def connect_session(device_setup, do_emulation: bool = False) -> Session:
    """Create and connect a `Session` for `device_setup`."""
    session = Session(device_setup)
    session.connect(do_emulation=do_emulation)
    return session


def init_data_saving(
    sample_name: str,
    cooldown_start_date: str,
    qubit_name: str,
    root: str = DEFAULT_DATA_ROOT,
) -> tuple[str, str]:
    """Create the per-qubit data directory and compute the shared QPU file path.

    Returns `(data_root_directory, qpu_file_path)`. `qpu_file_path` is shared
    by all qubits of a cooldown, so all four template notebooks compute it
    the same way from the same three identifiers.
    """
    cooldown_dir = os.path.join(root, sample_name, f"COOLDOWN_{cooldown_start_date}")
    data_root_directory = os.path.join(cooldown_dir, qubit_name)
    qpu_file_path = os.path.join(cooldown_dir, f"{sample_name}_qpu.json")

    os.makedirs(data_root_directory, exist_ok=True)

    print(f"Saving data to: {data_root_directory}")
    print(f"Saving/loading global parameters at: {qpu_file_path}")
    return data_root_directory, qpu_file_path


def setup_logbook(data_root_directory: str):
    """Activate the LabOne Q `FolderStore`/`LoggingStore` logbooks.

    Returns `(folder_store, logging_store)`; pass both to
    `logging_disabled` to temporarily suppress per-iteration logbook entries
    during a sweep loop.
    """
    folder_store = workflow.logbook.FolderStore(data_root_directory)
    folder_store.activate()

    logging_store = LoggingStore()
    logging_store.activate()
    return folder_store, logging_store


@contextmanager
def logging_disabled(folder_store, logging_store):
    """Temporarily deactivate the LabOne Q `FolderStore`/`LoggingStore` logbooks.

    Wrap any cell that runs an `experiment_workflow` (or similar) repeatedly
    inside a `for`/`while` loop with this context manager, so that LabOne Q
    does not write one logbook entry (notebook snapshot + all raw results)
    per sweep point. Re-activates both stores on exit, even if the loop body
    raises.

    Example:
        ```python
        with setup.logging_disabled(folder_store, logging_store):
            for value in sweep_values:
                ...  # run an experiment_workflow per iteration
        ```
    """
    folder_store.deactivate()
    logging_store.deactivate()
    try:
        yield
    finally:
        folder_store.activate()
        logging_store.activate()
