"""qmeas: lightweight qubit-measurement sample and parameter management.

This package provides the small helper objects used throughout the
measurement notebooks (e.g. ``S3_Q2_Cooldown_2.ipynb``)::

    from qmeas.qsample import QSample
    from qmeas.qparameters import QBaseParameters, QLinkedParameters

* :class:`~qmeas.qsample.QSample` describes *where* a given sample/structure
  lives on disk (used to build the ``.../parameters`` directory).
* :class:`~qmeas.qparameters.QBaseParameters` is a ``dict`` of named
  parameters (qubit parameters, LO settings, ...) tied to a
  :class:`QSample`, with convenience methods such as ``update_parameter`` and
  JSON save/load.
* :class:`~qmeas.qparameters.QLinkedParameters` extends ``QBaseParameters``
  with fallback resolution against one or more linked parameter sets.
"""

from .qsample import QSample
from .qparameters import QBaseParameters, QLinkedParameters

__all__ = ["QSample", "QBaseParameters", "QLinkedParameters"]
