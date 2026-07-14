"""Named parameter containers used by :mod:`qmeas`.

The notebooks group qubit-control/readout parameters and LO settings into
:class:`QBaseParameters` objects::

    qubit_parameters = QBaseParameters(
        sample=qsample_params,
        name=f'qubit_parameters_cooldown_{cooldown_nr}',
        parameters={'ro_freq': 136e6, 'ro_amp': 0.5, ...},
    )

    # read / write like a dict
    f = qubit_parameters['ro_freq']
    qubit_parameters['flux_point'] = 0.19e-3

    # or through the explicit helpers
    qubit_parameters.update_parameter('ro_freq', 135.9e6)
    qubit_parameters.add_parameter('pihalf_amp', 0.25)

    # the raw mapping (used e.g. as ``Data.update(qubit_parameters._params)``)
    all_pars = qubit_parameters._params

``QBaseParameters`` subclasses :class:`dict` so that existing notebook code
keeps working unchanged, in particular direct JSON serialisation
``json.dump(qubit_parameters, fp)`` and ``some_dict.update(qubit_parameters)``.
"""

from __future__ import annotations

import json
import os
import time
from typing import Iterable, Mapping, Optional, Union

timestamp = time.strftime("%Y-%m-%d-%H:%M:%S")

class QBaseParameters(dict):
    """A named set of measurement parameters bound to a :class:`QSample`.

    Behaves like a regular ``dict`` (indexing, ``update``, iteration, JSON
    serialisation) and additionally stores the owning ``sample`` and ``name``
    and exposes convenience helpers.

    Parameters
    ----------
    sample:
        The :class:`~qmeas.qsample.QSample` this parameter set belongs to.
        Optional, but required for :meth:`save`/:meth:`load` without an
        explicit directory.
    name:
        Name of the parameter set (used as the file stem when saving, e.g.
        ``'qubit_parameters_cooldown_2'``).
    parameters:
        Initial mapping of parameter name -> value.
    """

    def __init__(
        self,
        sample=None,
        name: Optional[str] = None,
        parameters: Optional[Mapping] = None,
    ):
        super().__init__(parameters if parameters is not None else {})
        self.sample = sample
        self.name = name

    # -- raw mapping access ---------------------------------------------
    @property
    def _params(self) -> "QBaseParameters":
        """The underlying parameter mapping.

        Kept for backwards compatibility with notebook code that does
        ``Data.update(qubit_parameters._params)``. It returns ``self`` (the
        object *is* the parameter mapping), so it is equivalent to passing the
        object directly.
        """
        return self

    # -- explicit helpers ------------------------------------------------
    def update_parameter(self, name: str, value):
        """Set ``name`` to ``value`` (creating it if it does not exist)."""
        self[name] = value
        return value

    def add_parameter(self, name: str, value):
        """Add a new parameter ``name`` with ``value``.

        Existing parameters are overwritten (a permissive behaviour so that
        repeated notebook cells do not raise).
        """
        self[name] = value
        return value

    def get_parameter(self, name: str, default=None):
        """Return the value of ``name`` (or ``default`` if not present)."""
        return self.get(name, default)

    def to_dict(self) -> dict:
        """Return a plain ``dict`` copy of the parameters."""
        return dict(self)

    # -- persistence -----------------------------------------------------
    def _resolve_directory(self, directory: Optional[str]) -> str:
        if directory is not None:
            return directory
        if self.sample is not None:
            return self.sample.parameters_dir
        return os.getcwd()

    def save(
        self,
        directory: Optional[str] = None,
        name: Optional[str] = None,
        ext: str = ".txt",
        indent: int = 4,
    ) -> str:
        """Serialise the parameters to ``<directory>/<name><ext>`` as JSON.

        Defaults to ``sample.parameters_dir`` and ``self.name``, matching the
        files the notebooks load with ``json.load``.
        """
        name = name if name is not None else self.name
        if name is None:
            raise ValueError("A 'name' is required to save parameters.")
        directory = self._resolve_directory(directory)
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, f"{name}{ext}")
        with open(path, "w") as fp:
            json.dump(dict(self), fp, indent=indent)
        return path

    @classmethod
    def load(
        cls,
        sample=None,
        name: Optional[str] = None,
        directory: Optional[str] = None,
        ext: str = ".txt",
    ) -> "QBaseParameters":
        """Load a parameter set previously written by :meth:`save`."""
        if name is None:
            raise ValueError("A 'name' is required to load parameters.")
        if directory is None:
            directory = sample.parameters_dir if sample is not None else os.getcwd()
        path = os.path.join(directory, f"{name}{ext}")
        with open(path, "r") as fp:
            parameters = json.load(fp)
        return cls(sample=sample, name=name, parameters=parameters)

    # -- display ---------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable listing of every stored parameter.

        Rendered as::

            --- <name> ---
            <key>: <value>
            ...

        This is what is shown when the object is evaluated on its own in a
        Jupyter cell / REPL (both use ``__repr__``) or printed.
        """
        header = f"--- {self.name} ---"
        dates = f"timestamp: {timestamp}"
        lines = [f"{key}: {value}" for key, value in self.items()]
        return "\n".join([header, dates, *lines])

    # Jupyter/REPL display and ``print`` should both use the listing above.
    __repr__ = __str__


class QLinkedParameters(QBaseParameters):
    """A :class:`QBaseParameters` that falls back to other parameter sets.

    In addition to its own parameters, a ``QLinkedParameters`` can be
    *linked* to one or more other parameter sets. When a key is not found in
    the object itself, it is looked up (in order) in the linked sets. This is
    convenient for deriving a per-experiment parameter set from a shared base
    set without copying every value.

    Parameters
    ----------
    sample, name, parameters:
        Same as :class:`QBaseParameters`.
    links:
        A single parameter set or an iterable of parameter sets to fall back
        on. They are consulted in the given order.
    """

    def __init__(
        self,
        sample=None,
        name: Optional[str] = None,
        parameters: Optional[Mapping] = None,
        links: Optional[Union[Mapping, Iterable[Mapping]]] = None,
    ):
        super().__init__(sample=sample, name=name, parameters=parameters)
        self.links = []
        if links is not None:
            if isinstance(links, Mapping):
                links = [links]
            self.links.extend(links)

    def add_link(self, other: Mapping) -> "QLinkedParameters":
        """Add ``other`` as a fallback parameter set."""
        self.links.append(other)
        return self

    def __missing__(self, key):
        # Called by dict.__getitem__ when ``key`` is not stored locally.
        for source in self.links:
            try:
                return source[key]
            except KeyError:
                continue
        raise KeyError(key)

    def __contains__(self, key) -> bool:
        if super().__contains__(key):
            return True
        return any(key in source for source in self.links)

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def resolved(self) -> dict:
        """Return a plain ``dict`` with links merged under local values."""
        merged: dict = {}
        for source in self.links:
            merged.update(dict(source))
        merged.update(dict(self))
        return merged
