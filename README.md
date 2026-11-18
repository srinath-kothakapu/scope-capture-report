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
