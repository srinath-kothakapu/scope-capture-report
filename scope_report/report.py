"""Write CSV, PNG plot, Markdown and HTML report."""
import csv
import html
import json
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

UNITS = {"vpp_v": "V", "v_low_v": "V", "v_high_v": "V", "v_mean_v": "V",
         "v_rms_v": "V", "frequency_hz": "Hz", "rise_time_s": "s"}


def _fmt(x):
    if x is None:
        return "-"
    return f"{x:.4g}"


def write_report(wf, results, checks, out_dir, source):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    with open(out / "capture.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_s", "voltage_v"])
        w.writerows(zip(wf.t, wf.v))

    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(wf.t * 1e6, wf.v, lw=0.9)
    ax.set_xlabel("Time (µs)")
    ax.set_ylabel("Voltage (V)")
    ax.set_title(f"Channel {wf.channel}")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / "waveform.png", dpi=150)
    plt.close(fig)

    (out / "results.json").write_text(json.dumps({"results": results, "checks": checks}, indent=2))

    overall = "PASS" if checks and all(c["pass"] for c in checks) else ("FAIL" if checks else "NO LIMITS")
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = [f"# Oscilloscope test report", "",
          f"- Date: {stamp}", f"- Source: {source}", f"- Instrument: {wf.idn}",
          f"- Channel: {wf.channel}", f"- Samples: {len(wf.v)}", f"- Result: **{overall}**", "",
          "## Measurements", "", "| Measurement | Value | Unit |", "|---|---|---|"]
    for k, v in results.items():
        md.append(f"| {k} | {_fmt(v)} | {UNITS.get(k, '')} |")
    if checks:
        md += ["", "## Limit checks", "", "| Measurement | Value | Min | Max | Result |", "|---|---|---|---|---|"]
        for c in checks:
            md.append(f"| {c['name']} | {_fmt(c['value'])} | {_fmt(c['min'])} | {_fmt(c['max'])} | "
                      f"{'PASS' if c['pass'] else 'FAIL'} |")
    md += ["", "![waveform](waveform.png)", ""]
    (out / "report.md").write_text("\n".join(md))

    rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{_fmt(v)}</td><td>{UNITS.get(k, '')}</td></tr>"
                   for k, v in results.items())
    crow = "".join(f"<tr><td>{html.escape(c['name'])}</td><td>{_fmt(c['value'])}</td><td>{_fmt(c['min'])}</td>"
                   f"<td>{_fmt(c['max'])}</td><td style='color:{'green' if c['pass'] else 'red'}'>"
                   f"{'PASS' if c['pass'] else 'FAIL'}</td></tr>" for c in checks)
    page = f"""<!doctype html><meta charset="utf-8"><title>Oscilloscope test report</title>
<style>body{{font-family:sans-serif;max-width:800px;margin:2em auto}}table{{border-collapse:collapse}}
td,th{{border:1px solid #bbb;padding:4px 10px}}</style>
<h1>Oscilloscope test report</h1>
<p>Date: {stamp}<br>Source: {html.escape(source)}<br>Instrument: {html.escape(wf.idn)}<br>
Channel: {wf.channel}, samples: {len(wf.v)}<br>Result: <b>{overall}</b></p>
<h2>Measurements</h2><table><tr><th>Measurement</th><th>Value</th><th>Unit</th></tr>{rows}</table>
<h2>Limit checks</h2><table><tr><th>Measurement</th><th>Value</th><th>Min</th><th>Max</th><th>Result</th></tr>{crow}</table>
<p><img src="waveform.png" width="800"></p>"""
    (out / "report.html").write_text(page)
    return overall
