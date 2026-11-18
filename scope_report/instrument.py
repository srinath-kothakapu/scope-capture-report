"""Oscilloscope access over SCPI.

The commands follow the Rigol DS1000Z-style waveform interface (:WAV:SOUR, :WAV:FORM,
:WAV:PRE?, :WAV:DATA?). Other vendors use similar but not identical commands, so check
the programming guide of your scope and adjust `capture()` if needed.
"""
from dataclasses import dataclass

import numpy as np


@dataclass
class Waveform:
    t: np.ndarray  # seconds
    v: np.ndarray  # volts
    channel: int
    idn: str


def open_scope(resource_name: str, timeout_ms: int = 10000):
    """Open a real instrument through pyvisa (e.g. 'TCPIP0::192.168.1.50::INSTR')."""
    import pyvisa  # imported here so the simulator and the tests work without VISA

    rm = pyvisa.ResourceManager()
    inst = rm.open_resource(resource_name)
    inst.timeout = timeout_ms
    return inst


def capture(inst, channel: int = 1) -> Waveform:
    """Read one screen of waveform data from `channel` and convert it to volts."""
    idn = inst.query("*IDN?").strip()
    inst.write(":STOP")
    inst.write(f":WAV:SOUR CHAN{channel}")
    inst.write(":WAV:MODE NORM")
    inst.write(":WAV:FORM BYTE")
    pre = inst.query(":WAV:PRE?").strip().split(",")
    n_points = int(float(pre[2]))
    x_inc, x_origin, x_ref = float(pre[4]), float(pre[5]), float(pre[6])
    y_inc, y_origin, y_ref = float(pre[7]), float(pre[8]), float(pre[9])

    raw = inst.query_binary_values(":WAV:DATA?", datatype="B", container=np.array)
    raw = np.asarray(raw, dtype=float)[:n_points]

    v = (raw - y_origin - y_ref) * y_inc
    t = (np.arange(len(raw)) - x_ref) * x_inc + x_origin
    inst.write(":RUN")
    return Waveform(t=t, v=v, channel=channel, idn=idn)
