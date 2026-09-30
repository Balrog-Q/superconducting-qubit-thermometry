"""Shared `.mat` payload building/saving helpers.

Every "Update Parameters"/data-saving cell in the original notebook repeated
the same boilerplate: merge experiment-specific arrays with the qubit's
scalar parameters and the sample/qubit/cooldown identifiers, then
`scipy.io.savemat(...)`. `build_mat_payload`/`save_mat` factor that out.
"""

from __future__ import annotations

from pathlib import Path

import attrs
import numpy as np
from scipy.io import loadmat, savemat


def build_mat_payload(
    qubit,
    sample_name: str,
    qubit_name: str,
    cooldown_start_date: str,
    data: dict | None = None,
    comment: str | None = None,
) -> dict:
    """Merge experiment `data` with the qubit's scalar parameters and sample metadata.

    `data` (if given) takes precedence over `comment`/metadata keys of the
    same name; qubit parameters are added last-but-do-not-overwrite anything
    already present in `data`, matching the original per-cell behaviour of
    `data.update({k: v for k, v in attrs.asdict(qubit.parameters).items() ...})`.
    """
    payload: dict = dict(data) if data is not None else {}
    if comment is not None:
        payload.setdefault("comment", comment)

    payload.update(
        {
            k: v
            for k, v in attrs.asdict(qubit.parameters).items()
            if isinstance(v, (int, float, str))
        }
    )
    payload["sample_name"] = sample_name
    payload["qubit_name"] = qubit_name
    payload["cooldown_start_date"] = cooldown_start_date
    return payload


def save_mat(file_path: str, payload: dict) -> str:
    """Save `payload` to `file_path` with `scipy.io.savemat` and print a confirmation."""
    savemat(file_path, payload)
    print(f"Saved data to: {file_path}")
    return file_path


def update_shots_mat(file_path: str, shots) -> None:
    """Append a new row of single shots to `file_path`'s `shots_g` array.

    Creates the file (and its parent directory) if it does not exist yet.
    Used by SINIS heating-with-SSRO sweeps to accumulate one row of shots per
    bias point into a single `.mat` file per state, instead of one file per
    LabOne Q workflow run.
    """
    file_path = Path(file_path)
    shots = np.asarray(shots)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    if file_path.exists():
        data = loadmat(file_path)
        if "shots_g" in data:
            data["shots_g"] = np.vstack([data["shots_g"], shots.reshape(1, -1)])
        else:
            data["shots_g"] = shots.reshape(1, -1)
    else:
        data = {"shots_g": shots.reshape(1, -1)}

    savemat(file_path, data)
