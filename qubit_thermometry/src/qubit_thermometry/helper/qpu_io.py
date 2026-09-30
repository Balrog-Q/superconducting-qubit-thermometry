"""Saving/loading the QPU and summarizing what a tune-up run produced.

Only the tune-up notebook builds a QPU from scratch; the other three
notebooks call `load_qpu` to pick up where tune-up left off, and continue
saving updates back to the same file with `save_qpu` whenever they still
adjust QPU parameters (e.g. readout tuning during single-shot measurements).
"""

from __future__ import annotations

from pprint import pprint

import attrs
from laboneq.serializers import load, save


def save_qpu(qpu, qpu_file_path: str) -> None:
    """Persist `qpu` (qubits + quantum operations) to `qpu_file_path`."""
    save(qpu, qpu_file_path)


def load_qpu(qpu_file_path: str):
    """Load a QPU previously saved with `save_qpu` (usually by the tune-up notebook)."""
    return load(qpu_file_path)


def print_qpu_summary(qpu, qpu_file_path: str, tuning_log: list[str] | None = None) -> None:
    """Print the final tuned parameters, what was tuned, and the save path.

    Intended for the last cell of the tune-up notebook. `tuning_log` is a
    plain list of short strings that the notebook appends to after each
    "Update Parameters" cell, e.g.
    `tuning_log.append("Resonator Spectroscopy -> readout_resonator_frequency")`.
    """
    print("=" * 70)
    print("Tune-up summary")
    print("=" * 70)

    for qubit in qpu.quantum_elements:
        print(f"\nQubit: {qubit.uid}")
        pprint(attrs.asdict(qubit.parameters))

    if tuning_log:
        print("\nExperiments run (in order):")
        for i, entry in enumerate(tuning_log, start=1):
            print(f"  {i}. {entry}")
    else:
        print("\nNo tuning steps were recorded in `tuning_log`.")

    print(f"\nTuned QPU saved to: {qpu_file_path}")
