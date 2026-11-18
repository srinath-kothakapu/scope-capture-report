import numpy as np
import pytest

from scope_report.analysis import check_limits, frequency, measure, rise_time
from scope_report.cli import main
from scope_report.instrument import capture
from scope_report.simulator import SimulatedScope


def test_frequency_of_sine():
    t = np.arange(0, 1e-3, 1e-7)
    v = np.sin(2 * np.pi * 5e3 * t)
    assert frequency(t, v) == pytest.approx(5e3, rel=1e-3)


def test_rise_time_of_known_rc_edge():
    tau = 1e-6
    t = np.arange(0, 1e-5, 1e-8)
    v = np.where(t < 1e-6, 0.0, 1 - np.exp(-(t - 1e-6) / tau))
    # 10-90 % rise time of an RC step is 2.197 * tau
    assert rise_time(t, v) == pytest.approx(2.197 * tau, rel=0.05)


def test_capture_from_simulator_converts_to_volts():
    wf = capture(SimulatedScope(), channel=1)
    assert wf.idn.startswith("SIM")
    assert len(wf.t) == len(wf.v) == 1200
    assert wf.v.max() == pytest.approx(3.3, abs=0.2)
    assert wf.t[1] - wf.t[0] == pytest.approx(50e-9)


def test_simulated_measurements_close_to_truth():
    wf = capture(SimulatedScope(), 1)
    r = measure(wf.t, wf.v)
    assert r["frequency_hz"] == pytest.approx(100e3, rel=0.01)
    assert r["rise_time_s"] == pytest.approx(2.197 * 136e-9, rel=0.2)


def test_limits_pass_and_fail():
    r = {"frequency_hz": 100e3, "vpp_v": 3.3}
    ok = check_limits(r, {"frequency_hz": {"min": 99e3, "max": 101e3}})
    bad = check_limits(r, {"vpp_v": {"max": 3.0}})
    assert ok[0]["pass"] and not bad[0]["pass"]


def test_missing_measurement_fails():
    assert not check_limits({}, {"vpp_v": {"min": 1}})[0]["pass"]


def test_cli_end_to_end(tmp_path):
    rc = main(["--sim", "--limits", "examples/limits_100khz_clock.json", "--out", str(tmp_path)])
    assert rc == 0
    for f in ["report.md", "report.html", "waveform.png", "capture.csv", "results.json"]:
        assert (tmp_path / f).exists()
    assert "PASS" in (tmp_path / "report.md").read_text()
