import argparse
import json
import sys

from .analysis import check_limits, measure
from .instrument import capture, open_scope
from .report import write_report
from .simulator import SimulatedScope


def main(argv=None):
    p = argparse.ArgumentParser(prog="scope-report",
                                description="Capture a scope waveform over SCPI and write a test report.")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--resource", help="VISA resource, e.g. TCPIP0::192.168.1.50::INSTR")
    src.add_argument("--sim", action="store_true", help="use the built-in simulated scope")
    p.add_argument("--channel", type=int, default=1)
    p.add_argument("--limits", help="JSON file with pass/fail limits")
    p.add_argument("--out", default="report_out")
    a = p.parse_args(argv)

    inst = SimulatedScope() if a.sim else open_scope(a.resource)
    wf = capture(inst, a.channel)
    results = measure(wf.t, wf.v)
    limits = json.load(open(a.limits)) if a.limits else {}
    checks = check_limits(results, limits)
    overall = write_report(wf, results, checks, a.out, "simulator" if a.sim else a.resource)
    print(f"Report written to {a.out}/ : {overall}")
    return 0 if overall != "FAIL" else 1


if __name__ == "__main__":
    sys.exit(main())
