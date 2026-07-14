"""Sample description used by :mod:`qmeas`.

A :class:`QSample` bundles the three pieces of information needed to locate a
measured structure on disk: the root ``directory``, the ``sample`` name and
the ``structure`` name. It is created in the notebooks as::

    qsample_params = QSample(directory=sample_parameters['folder_name'],
                             sample=sample_parameters['sample_name'],
                             structure=sample_parameters['structure_name'])

and is handed to :class:`~qmeas.qparameters.QBaseParameters` so parameter sets
know where to be saved/loaded. Parameter files live in
``<directory>/<sample>/<structure>/parameters``, matching the ``root_dir``
built by hand in the notebooks.
"""

from __future__ import annotations

import os
from typing import Optional


class QSample:
    """Location of a sample/structure on disk.

    Parameters
    ----------
    directory:
        Root data directory (e.g. ``r'N:\\xld\\Kubatkin\\Data'``).
    sample:
        Sample name (e.g. ``'S3'``).
    structure:
        Structure/qubit name (e.g. ``'Q2'``).
    """

    #: Sub-folder (relative to the structure directory) that holds parameters.
    PARAMETERS_SUBDIR = "parameters"

    def __init__(self, directory: str, sample: str, structure: str):
        self.directory = directory
        self.sample = sample
        self.structure = structure

    # -- derived paths ---------------------------------------------------
    @property
    def path(self) -> str:
        """``<directory>/<sample>/<structure>``."""
        return os.path.join(self.directory, self.sample, self.structure)

    @property
    def parameters_dir(self) -> str:
        """Directory holding the parameter files for this structure."""
        return os.path.join(self.path, self.PARAMETERS_SUBDIR)

    def parameter_path(self, name: str, ext: str = ".txt") -> str:
        """Full path of the parameter file ``name`` (with extension ``ext``)."""
        return os.path.join(self.parameters_dir, f"{name}{ext}")

    def make_dirs(self) -> "QSample":
        """Create the sample/structure/parameters directories if missing."""
        os.makedirs(self.parameters_dir, exist_ok=True)
        return self

    # -- dunder helpers --------------------------------------------------
    def as_dict(self) -> dict:
        return {
            "directory": self.directory,
            "sample": self.sample,
            "structure": self.structure,
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QSample):
            return NotImplemented
        return self.as_dict() == other.as_dict()

    def __hash__(self) -> int:
        return hash((self.directory, self.sample, self.structure))

    def __repr__(self) -> str:
        return (
            f"QSample(directory={self.directory!r}, sample={self.sample!r}, "
            f"structure={self.structure!r})"
        )
