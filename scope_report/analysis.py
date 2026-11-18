"""Measurements on a captured waveform."""
import numpy as np


def _levels(v):
    """Low and high level from the 5th and 95th percentile (robust against overshoot/noise)."""
    return float(np.percentile(v, 5)), float(np.percentile(v, 95))


def frequency(t, v):
    """Frequency from rising zero crossings of the mid level, with linear interpolation."""
    low, high = _levels(v)
    mid = (low + high) / 2
    above = v >= mid
    idx = np.where(~above[:-1] & above[1:])[0]
    if len(idx) < 2:
        return float("nan")
    cross = t[idx] + (mid - v[idx]) / (v[idx + 1] - v[idx]) * (t[idx + 1] - t[idx])
    return float(1.0 / np.mean(np.diff(cross)))


def rise_time(t, v):
    """Average 10 % to 90 % rise time over all rising edges."""
    low, high = _levels(v)
    amp = high - low
    if amp <= 0:
        return float("nan")
    l10, l90 = low + 0.1 * amp, low + 0.9 * amp
    times = []
    i = 0
    while i < len(v) - 1:
        if v[i] <= l10:
            j = i
            while j < len(v) - 1 and v[j] < l90:
                j += 1
            if v[j] >= l90:
                # last sample below 10 % before the crossing and first at/above 90 %
                k = j
                while k > i and v[k - 1] > l10:
                    k -= 1
                t10 = t[k - 1] + (l10 - v[k - 1]) / (v[k] - v[k - 1]) * (t[k] - t[k - 1]) if k > 0 else t[k]
                t90 = t[j - 1] + (l90 - v[j - 1]) / (v[j] - v[j - 1]) * (t[j] - t[j - 1])
                times.append(t90 - t10)
            i = j + 1
        else:
            i += 1
    return float(np.mean(times)) if times else float("nan")


def measure(t, v):
    low, high = _levels(v)
    return {
        "vpp_v": float(np.max(v) - np.min(v)),
        "v_low_v": low,
        "v_high_v": high,
        "v_mean_v": float(np.mean(v)),
        "v_rms_v": float(np.sqrt(np.mean(v ** 2))),
        "frequency_hz": frequency(t, v),
        "rise_time_s": rise_time(t, v),
    }


def check_limits(results, limits):
    """limits: {"frequency_hz": {"min": .., "max": ..}, ...}. Returns a list of rows."""
    rows = []
    for key, lim in limits.items():
        value = results.get(key, float("nan"))
        lo, hi = lim.get("min"), lim.get("max")
        ok = not np.isnan(value) and (lo is None or value >= lo) and (hi is None or value <= hi)
        rows.append({"name": key, "value": value, "min": lo, "max": hi, "pass": bool(ok)})
    return rows
