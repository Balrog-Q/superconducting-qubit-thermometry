"""Shared, dependency-light helper functions used by every template notebook.

Modules are organized by functionality (not by which experiment first needed
them), since several of them are reused across multiple template notebooks:

- ``setup``: device/session setup, data-saving bootstrap, generic sweep utils.
- ``qpu_io``: saving/loading the QPU and summarizing tuned parameters.
- ``data_io``: building/saving the ``.mat`` payloads used by "Update
  Parameters" cells.
- ``fitting``: curve-fitting helpers (oscillations, exponential decay, linear).
- ``temperature``: population -> pe/pg -> effective-temperature calculations.
- ``plotting``: shared temperature/statistics/2D plotting helpers.
- ``single_shot``: IQ-blob single-shot analysis helpers.
- ``sinis_devices``: DC-instrument connection helpers for SINIS calibration.
"""
