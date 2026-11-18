"""A small fake oscilloscope so the tool and the tests run without hardware.

It answers the same SCPI commands as `instrument.capture()` uses and returns a noisy
100 kHz square wave with a finite rise time, quantised to 8 bit like a real scope.
This is a simulation. It does not prove the code works on a real instrument.
"""
import numpy as np


class SimulatedScope:
    def __init__(self, freq_hz=100e3, v_low=0.0, v_high=3.3, rise_tau_s=136e-9,
                 noise_v=0.02, n_points=1200, x_inc=50e-9, seed=1):
        self.freq_hz, self.v_low, self.v_high = freq_hz, v_low, v_high
        self.rise_tau_s, self.noise_v = rise_tau_s, noise_v
        self.n_points, self.x_inc = n_points, x_inc
        self.y_inc, self.y_ref = 0.04, 127.0
        self._rng = np.random.default_rng(seed)
        self.log = []

    # --- instrument interface used by capture() ---
    def write(self, cmd):
        self.log.append(cmd)

    def query(self, cmd):
        self.log.append(cmd)
        if cmd == "*IDN?":
            return "SIM,SimulatedScope,0001,0.1\n"
        if cmd == ":WAV:PRE?":
            return (f"0,0,{self.n_points},1,{self.x_inc},0,0,"
                    f"{self.y_inc},0,{self.y_ref}\n")
        raise ValueError(f"unknown query {cmd}")

    def query_binary_values(self, cmd, datatype="B", container=np.array):
        self.log.append(cmd)
        v = self._signal()
        codes = np.clip(np.round(v / self.y_inc + self.y_ref), 0, 255).astype(np.uint8)
        return container(codes)

    # --- signal model ---
    def _signal(self):
        t = np.arange(self.n_points) * self.x_inc
        period = 1.0 / self.freq_hz
        phase = (t % period) / period
        target = np.where(phase < 0.5, self.v_high, self.v_low)
        # first-order low-pass (RC) gives a realistic rise and fall time
        alpha = 1.0 - np.exp(-self.x_inc / self.rise_tau_s)  # exact discretisation of an RC filter
        v = np.empty_like(target)
        v[0] = target[0]
        for i in range(1, len(target)):
            v[i] = v[i - 1] + alpha * (target[i] - v[i - 1])
        return v + self._rng.normal(0, self.noise_v, size=v.shape)
