# Quickstart Guide

This guide walks you through setting up and running the superconducting qubit thermometry experiments.

## Prerequisites

- **Python 3.10–3.12** (required by LabOne Q)
- **Zurich Instruments LabOne** software installed and running on the dataserver host
- Network access to all instruments (SHFQC, Yokogawa, SIM900, Keysight DMM/WG, BlueFors XLD)
- A working dilution refrigerator with the sample mounted and wired

## 1. Clone / Copy the Project

```bash
cd ~/Desktop
# If using git:
git clone <repo-url> superconducting-qubit-thermometry
# Otherwise, just copy the folder as-is.
cd superconducting-qubit-thermometry
```

## 2. Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Key packages:

| Package | Purpose |
|---|---|
| `laboneq` | Zurich Instruments QCCS experiment SDK |
| `numpy`, `scipy`, `matplotlib` | Numerical computing, fitting, plotting |
| `scikit-learn` | PCA for IQ-data rotation |
| `pyvisa` + `pyvisa-py` | Instrument communication (GPIB/TCP) |
| `requests` | HTTP client for BlueFors XLD fridge |
| `playsound` | Audio notification when measurements finish |
| `jupyterlab` | Notebook environment |
| `ipykernel` | Jupyter kernel for the venv |

## 4. Register the Jupyter Kernel

```bash
python -m ipykernel install --user --name=qubit-thermo --display-name "Qubit Thermometry"
```

## 5. Configure Instrument Addresses

Open `S3_Q2_Cooldown_2.ipynb` and update the addresses to match your setup:

- **SHFQC**: in `lib/helpers/setup_helper.py`, update the `address: DEV12192` line in `my_descriptor`.
- **LabOne Q dataserver**: in the notebook's "Create and Connect to a LabOne Q Session" cell, update the `server_host` parameter.
- **Yokogawa GS200**: update `Yoko_addr` (default: `TCPIP0::192.168.1.201::inst0::INSTR`).
- **SIM900**: update the VISA address in the SIM setup cells.
- **Keysight 34465A / 33622A**: update VISA addresses in the SINIS section.
- **BlueFors XLD**: update `server_ip` in the temperature controller cells, and credentials in `lib/devices/bftc_credentials.py` and `XLD_Server_Passkey.py`.

## 6. Set Sample Parameters

In the notebook's "Sample parameters" section, update:

```python
sample_parameters = {
    'folder_name': r'/path/to/your/data/root',
    'sample_name': r'YourSampleName',
    'structure_name': r'YourQubitName',
}
```

## 7. Set Qubit Parameters

In the "Qubit and LO parameters" section, enter your qubit's known (or estimated) parameters:

```python
qubit_parameters = {
    'ro_freq': 136e6,        # readout IF frequency (Hz)
    'qb_freq': -110e6,       # qubit IF frequency (Hz)
    'qb_anharm': 200e6,      # anharmonicity (Hz)
    # ... (see notebook for full list)
}

lo_settings = {
    'qb_lo': 5.0e9,          # qubit drive LO (Hz)
    'ro_lo': 7.0e9,          # readout LO (Hz)
}
```

These will be refined through the spectroscopy and calibration steps.

## 8. Launch Jupyter and Run the Notebook

```bash
jupyter lab
```

Open `S3_Q2_Cooldown_2.ipynb` and select the **"Qubit Thermometry"** kernel.

### Recommended execution order

The notebook is designed to be run **top-to-bottom** through these phases:

1. **Initialisation** (cells 0–28): imports, instrument connections, parameter setup.
2. **Spectroscopy** (cells 29–86): find resonator and qubit frequencies.
   - Update `qubit_parameters` with fitted values after each spectroscopy step.
3. **Control Pulse Setup** (cells 87–246): calibrate g↔e and e↔f π/π/2 pulses.
   - Run Rabi → update pulse amplitudes → verify with error amplification.
   - Run T1, Ramsey, Echo to characterise coherence times.
4. **Readout Optimisation** (cells 248–327): tune readout for best state discrimination.
5. **Population Measurements** (cells 328–435): the core thermometry measurement.
   - Start with RPM calibration to validate the measurement protocol.
   - Run three-level population measurement.
   - Extract temperatures using `pop_temp_helper_v2`.
6. **Fast Flux Drive** (cells 437–516, optional): flux-tunable experiments.
7. **SINIS & Temperature Sweeps** (cells 517–668, optional): cross-calibration with SINIS thermometry.

### Running in emulation mode

To test the notebook without hardware, set `emulate = True` in the session creation cell:

```python
emulate = True
my_session = Session(device_setup=my_setup)
my_session.connect(do_emulation=emulate)
```

This will run the LabOne Q compiler and generate dummy data — useful for checking pulse sequences and analysis code.

## 9. Analysing Results Offline

The analysis helpers can be imported standalone without instrument connections:

```python
import sys
sys.path.insert(0, '/path/to/superconducting-qubit-thermometry')

from lib.helpers.fitting_helper import auto_T1_fit, auto_ramsey_fit
from lib.helpers.pop_temp_helper_v2 import make_all_temperatures, get_stat
from lib.utils.calculator import n_T, chi
```

## Troubleshooting

- **`ModuleNotFoundError: No module named 'laboneq'`**: ensure you activated the virtual environment and installed requirements.
- **VISA connection errors**: check that instruments are powered on and reachable via `ping`. Verify addresses with `pyvisa`'s resource manager:
  ```python
  import pyvisa
  rm = pyvisa.ResourceManager()
  print(rm.list_resources())
  ```
- **`emulate = False` but no SHFQC found**: verify the LabOne dataserver is running and the device serial (`DEV12192`) is correct.
- **Notebook kernel dies on large data**: some cells generate large single-shot datasets; ensure sufficient RAM (≥16 GB recommended).
