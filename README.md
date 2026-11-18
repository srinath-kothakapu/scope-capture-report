# scope-capture-report

**Automatically capture a waveform from an oscilloscope, measure it, check it against limits, and get a test report.**

Python 3 · pyvisa · numpy · matplotlib · pytest

## What problem does this solve?

When you test an electronic circuit, you often look at a signal on an oscilloscope and read the numbers off the screen by hand: How big is the signal? What frequency is it? How fast is the edge? Then you write the results into a report.

This tool does those steps automatically and the same way every time:

```
Oscilloscope  ──SCPI commands──▶  capture waveform  ──▶  measure  ──▶  compare with limits  ──▶  report
 (or simulator)    (pyvisa)       (raw bytes → volts)   (Vpp, freq,     (PASS / FAIL)          (Markdown, HTML,
                                                          rise time…)                           PNG, CSV, JSON)
```

## What you get

For one captured channel the tool measures:

| Measurement | Meaning |
|---|---|
| Vpp | Peak-to-peak voltage |
| Low / high level | Typical "off" and "on" voltage of the signal |
| Mean and RMS | Average and effective voltage |
| Frequency | Calculated from the rising edges |
| Rise time | Time to go from 10 % to 90 % of the signal height |

It then checks each value against limits you define in a small JSON file and writes:

- `report.md` and `report.html`: the test report with PASS/FAIL
- `waveform.png`: a plot of the signal
- `capture.csv`: the raw data (time, voltage)
- `results.json`: all results in machine-readable form

The program exits with code 1 if any limit fails, so it can be used inside a test script or CI.

## Important: what has and has not been tested

- **Tested:** all code runs and passes its tests against a **built-in simulated oscilloscope** (a noisy 100 kHz square wave with a realistic rise time).
- **Not tested:** I have **not** run this on a real oscilloscope yet.
- The SCPI commands follow the Rigol DS1000Z-style waveform interface (`:WAV:SOUR`, `:WAV:FORM`, `:WAV:PRE?`, `:WAV:DATA?`). Other brands use similar but different commands, so `capture()` in `scope_report/instrument.py` may need small changes.
- Rise time can only be as accurate as the scope's sample rate allows.

## Quick start (no oscilloscope needed)

```
git clone https://github.com/srinath-kothakapu/scope-capture-report.git
cd scope-capture-report
pip install -r requirements.txt

python -m scope_report --sim --limits examples/limits_100khz_clock.json --out report_out
```

Then open `report_out/report.html` (or `report.md`).

### With a real oscilloscope

```
python -m scope_report --resource "TCPIP0::192.168.1.50::INSTR" --channel 1 --limits examples/limits_100khz_clock.json
```

Replace the address with your scope's VISA address. For LAN or USB scopes without NI-VISA installed, the `pyvisa-py` backend in `requirements.txt` is used.

### Options

| Option | Meaning |
|---|---|
| `--sim` | Use the built-in simulated scope |
| `--resource` | VISA address of a real scope (use this or `--sim`) |
| `--channel` | Channel number, default 1 |
| `--limits` | JSON file with pass/fail limits |
| `--out` | Output folder, default `report_out` |

## Example result

From the simulator with the example limits (full file: `examples/sample_report/report.md`):

| Measurement | Value | Min | Max | Result |
|---|---|---|---|---|
| frequency_hz | 1e+05 | 9.9e+04 | 1.01e+05 | PASS |
| vpp_v | 3.44 | 3.2 | 3.8 | PASS |
| rise_time_s | 3.062e-07 | - | 5e-07 | PASS |

## Limits file

Each limit can have a `min`, a `max`, or both:

```json
{
  "frequency_hz": {"min": 99000, "max": 101000},
  "vpp_v":        {"min": 3.2,   "max": 3.8},
  "rise_time_s":  {"max": 5e-7}
}
```

Available names: `vpp_v`, `v_low_v`, `v_high_v`, `v_mean_v`, `v_rms_v`, `frequency_hz`, `rise_time_s`.

## Project layout

```
scope_report/
  instrument.py   talks to the scope (pyvisa/SCPI) and converts raw bytes to volts and seconds
  simulator.py    fake scope for running without hardware
  analysis.py     the measurements and the limit check
  report.py       writes the report files
  cli.py          command line interface
tests/            pytest tests
examples/         example limits file and a sample report
```

## Tests

```
python -m pytest
```

The 7 tests check frequency and rise time on signals with known values, the conversion of simulator data to volts, the pass/fail logic, and a full command-line run that creates all report files.

## Ideas for next steps

- Run it on a real scope and note which SCPI commands need changing
- Add jitter and eye-diagram measurements
- Add a second channel and a delay measurement between channels
# scope-capture-report

A small Python tool that reads a waveform from an oscilloscope over SCPI (pyvisa), measures it, checks the results against limits and writes a test report.

I wrote it to practise automated measurement and reporting, the kind of work that comes after setting up a scope by hand: capture, analyse, compare to limits, document.

## What it does

1. Connects to a scope through pyvisa (or to a built-in simulated scope).
2. Captures one screen of a channel and converts the raw bytes to volts and seconds.
3. Measures Vpp, low/high level, mean, RMS, frequency and 10–90 % rise time.
4. Compares the results with limits from a JSON file (pass/fail).
5. Writes `report.md`, `report.html`, `waveform.png`, `capture.csv` and `results.json`.

## Status, please read

- **I have only run this against the built-in simulator, not on a real oscilloscope.** The simulator is a noisy 100 kHz square wave with an RC rise time, quantised to 8 bit.
- The SCPI commands follow the Rigol DS1000Z-style waveform interface (`:WAV:SOUR`, `:WAV:FORM`, `:WAV:PRE?`, `:WAV:DATA?`). Other vendors differ, so you may need to change `capture()` in `scope_report/instrument.py`.
- Rise time is limited by the scope's sample rate. With very fast edges the number is only as good as the sampling.

## Install and run

```
pip install -r requirements.txt

# no hardware needed
python -m scope_report --sim --limits examples/limits_100khz_clock.json --out report_out

# real scope over LAN
python -m scope_report --resource "TCPIP0::192.168.1.50::INSTR" --channel 1 --limits examples/limits_100khz_clock.json
```

The exit code is 1 if a limit check fails, so it can run in a test script or CI.

A sample report from the simulator is in `examples/sample_report/report.md`.

## Tests

```
python -m pytest
```

The tests check frequency and rise time against signals with known values, the simulator capture, the limit logic and the whole command line run.

## Limits file

```json
{
  "frequency_hz": {"min": 99000, "max": 101000},
  "vpp_v":        {"min": 3.2,   "max": 3.8},
  "rise_time_s":  {"max": 5e-7}
}
```

## Ideas for next steps

- Try it on a real scope and note which SCPI commands need changing.
- Add jitter and eye-diagram measurements.
- Add a second channel and a delay measurement between channels.
