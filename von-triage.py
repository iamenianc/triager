#!/usr/bin/env python3
"""von-triage.py - triage score 1-5 for the life-insurance quoting platform (von decision model).

Two DISCRETE flows, chosen by the caller (no router - Ian's call):
  python von-triage.py defect  "<text>"    -> Tranche 1: software bugs & defects (24 questions)
  python von-triage.py feature "<text>"    -> Tranche 2: new feature requests (24 questions)

Each flow asks its branch's 24 yes/no probes (8 groups x 3, from von_branches.py).
von returns a probability 0-1 per probe (noul). No rounding in any step: the 24
floats are summed directly (range 0-24, continuous) - two reversed-polarity probes
in the Workaround group contribute (1 - p) - and the exact sum is compared against
the band thresholds (per-flow).

Band calibration (60-case domain battery): no-signal text lands at the uniform
mid of the range; moderate cases land mid-band; strong cases near the top.
Per-flow cuts below (each tranche has a different sum distribution).

Each probe contributes its probability as a float; the sum is continuous (0-24) and
is compared against the band cuts. Do not discretize probes or exclude mid-range
probabilities from the sum.

No regex stripping, no steering clause: the questions ask about consequences and
magnitude, not tone. Question wording is load-bearing; keep von_branches.py stable.

Usage:
    python von-triage.py defect  "The quoting engine shows wrong rider costs."
    python von-triage.py feature "Please add split-dollar funding solves."
    echo "text" | python von-triage.py defect
    python von-triage.py -m <model> defect "text"   (default model: von)

Requires the Ollaya server running with von loaded (ollaya run von starts it).
"""
import json, sys, urllib.request

from von_branches import DEFECT_QS, FEATURE_QS, DEFECT_INVERTED

URL = "http://localhost:11435/api/decide"

MODEL = "von"  # override with -m/--model

# Per-flow bands (calibrated by brute-force threshold search on the 60-case battery;
# the two tranches have different sum distributions, so each gets its own cuts).
# T1: 22/31 exact, 29/31 within 1. T2: 18/29 exact, 28/29 within 1
# (bands scoring varies by about 1 case between runs).
SUM_BANDS = {
    "defect":  [(5.0, 1), (6.4, 2), (8.8, 3), (11.0, 4), (999, 5)],
    "feature": [(2.5, 1), (4.3, 2), (6.9, 3), (12.0, 4), (999, 5)],
}


def post(state, questions):
    body = json.dumps({"model": MODEL, "state": state, "questions": questions}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["answers"]


def score(flow, state):
    branch = DEFECT_QS if flow == "defect" else FEATURE_QS
    inverted = DEFECT_INVERTED if flow == "defect" else set()
    qs = {k: {"type": "noul", "instructions": q} for k, q in branch.items()}
    ans = post(state, qs)
    # reversed-polarity probes: yes is good, so contribute (1 - p); everything else p
    perq = {k: (1.0 - float(v["noul"])) if k in inverted else float(v["noul"]) for k, v in ans.items()}
    total = sum(perq.values())
    for ceiling, band in SUM_BANDS[flow]:
        if total <= ceiling:
            return band, perq, total
    return 5, perq, total


def get_args():
    """returns (flow, text); flow is mandatory and first (after optional -m <model>)"""
    global MODEL
    args = sys.argv[1:]
    if args and args[0] in ("-m", "--model"):
        MODEL = args[1]
        args = args[2:]
    if not args or args[0] not in ("defect", "feature"):
        raise SystemExit('usage: von-triage.py defect "<text>"  |  von-triage.py feature "<text>"  |  echo text | von-triage.py defect')
    flow = args[0]
    args = args[1:]
    if args:
        return flow, " ".join(args)
    data = sys.stdin.read().strip()
    if data:
        return flow, data
    raise SystemExit('usage: von-triage.py defect "<text>"  |  echo text | von-triage.py defect')


def main():
    flow, text = get_args()
    band, perq, total = score(flow, text)
    label = "defect report (T1)" if flow == "defect" else "feature request (T2)"
    print("score    %d/5   [flow: %s, sum of 24 probes: %.2f/24]" % (band, label, total))
    branch = DEFECT_QS if flow == "defect" else FEATURE_QS
    for k in branch:
        print("  %.2f  %s" % (perq[k], k))


if __name__ == "__main__":
    main()
