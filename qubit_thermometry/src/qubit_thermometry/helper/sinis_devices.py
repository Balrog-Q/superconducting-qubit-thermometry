"""DC-measurement instrument connection helpers for the SINIS heating sweeps.

Replaces the "Setup Instruments for DC-Measurements" section that used to be
duplicated at the top of the SINIS Calibration part of the notebook
(``Workflow-v1.7.3.json`` cells 465-478): connecting to the BlueFors
temperature controller, the Keysight DMM used to read out the SINIS
thermometer voltage, and the SRS SIM900 frame supplying the heater bias
(``SIM928`` modules 1 and 2). Also factors out the "ramp with retry on
instrument-communication error" loop that preceded every bias sweep.
"""

from __future__ import annotations

import time

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from blueftc.BlueforsController import BlueFTController
from lib.devices.bftc_credentials import (
    BFTS_API_KEY,
    BFTS_IP,
    HEATER_ID,
    MXC_ID,
    PORT_NUMBER,
)
from lib.devices.KeysightDMM34465A import KeysightDMM34465A
from lib.devices.SIM_wrapper import SIM900


def connect_temperature_controller() -> BlueFTController:
    """Connect to the BlueFors temperature controller and return it.

    Disables `urllib3`'s "insecure request" warning, matching the original
    notebook (the BlueFors REST API is queried over `https` with a
    self-signed certificate).
    """
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    bft_controller = BlueFTController(
        ip=BFTS_IP,
        port=PORT_NUMBER,
        key=BFTS_API_KEY,
        mixing_chamber_channel_id=MXC_ID,
        controller_type="bluefors",
        mixing_chamber_heater_id=HEATER_ID,
    )
    return bft_controller


def connect_dc_voltmeter(address: str) -> KeysightDMM34465A:
    """Connect to the Keysight 34465A DMM used to read the SINIS thermometer voltage.

    Sets `NPLC=10`, matching the original notebook.
    """
    dmm = KeysightDMM34465A(address)
    dmm.set_nplc(10)
    return dmm


def connect_sim_voltage_source(frame_address: str):
    """Connect to the SRS SIM900 frame and return `(frame, sim, sim2)`.

    `sim`/`sim2` are the `SIM928` voltage sources plugged into frame ports 1
    and 2 respectively (heater bias for SINIS A and SINIS C).
    """
    frame = SIM900(address=frame_address)
    sim = frame.get_sim(1)
    sim2 = frame.get_sim(2)
    return frame, sim, sim2


def ramp_voltage_with_retry(sim, target_voltage: float, n_steps: int = 20, wait_time: float = 5) -> None:
    """Ramp `sim` to `target_voltage`, retrying on instrument-communication errors.

    Old `while k: try: sim.get_level(...); sim.ramp(...); except: time.sleep(wait_time)`
    loop that preceded every heater-bias sweep point (and the return-to-off
    ramp at the end of each sweep).
    """
    ramped = False
    while not ramped:
        try:
            sim.get_level(only_number=True)
            sim.ramp(target_voltage, N_steps=n_steps)
            ramped = True
        except Exception:
            print("Could not set voltage!")
            time.sleep(wait_time)
