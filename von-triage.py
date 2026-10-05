#!/usr/bin/env python3
"""von-triage.py - triage score 1-5 for the life-insurance quoting platform (von decision model).

Two DISCRETE flows, chosen by the caller (no router - Ian's call):
  python von-triage.py defect  "<text>"    -> Tranche 1: software bugs & defects
  python von-triage.py feature "<text>"    -> Tranche 2: new feature requests

Each flow asks its branch's 3 severity probes (from von_branches.py TRIAGE_PROBES):
  defect : dmg (destroys/corrupts/miscalculates data or money),
           block (stops work or forces redo),
           client_visible (happens in front of clients or affects client documents),
           all (meaningfully impacts 100% of the user base)
  feature: rev (missing it loses business), time (saves real daily time),
           manual (currently done by hand, in spreadsheets, or with outside tools),
           all (meaningfully impacts 100% of the user base)

von returns a probability 0-1 per probe (noul). No rounding in any step: the 4
floats are summed directly (range 0-4, continuous) and the exact sum is compared
against the per-flow band cuts.

Each probe contributes its probability as a float; the sum is continuous (0-4) and
is compared against the band cuts. Do not discretize probes or exclude mid-range
probabilities from the sum.

No regex stripping, no steering clause: the questions ask about consequences and
magnitude, not tone. Question wording is load-bearing; keep von_branches.py stable.

Band calibration (two 60-case batteries, one verbose professional style and one
terse intern style; cuts fitted by brute-force threshold search on the combined
120 cases; the two tranches have different sum distributions, so each gets its
own cuts). Accuracy on the combined A+B fit set (goal prefix + damage rules): defect 53%
exact, 93% within 1; feature 50% exact, 68% within 1. On battery C (unseen
conversational style) as a holdout: defect 39% exact, 81% within 1; feature
45% exact, 79% within 1. A one-band error is acceptable in triage; the goal
prefix trades peak accuracy on formal prose for steadier results on casual
writing styles, and the damage rules guarantee wrong money/data/privacy lands
at least 4 and usually 5 even in terse single-signal reports.

Usage:
    python von-triage.py defect  "The quoting engine shows wrong rider costs."
    python von-triage.py feature "Please add split-dollar funding solves."
    echo "text" | python von-triage.py defect
    python von-triage.py -m <model> defect "text"   (default model: von)

Requires the Ollaya server running with von loaded (ollaya run von starts it).
"""
import json, sys, urllib.request

from von_branches import TRIAGE_PROBES, TRIAGE_INVERTED

URL = "http://localhost:11435/api/decide"

MODEL = "von"  # override with -m/--model

# The 3 probes per flow, in fixed order (von is option-order sensitive).
PROBES = {flow: list(qs.keys()) for flow, qs in TRIAGE_PROBES.items()}

# Per-flow band cuts on the 0-4 float sum (fitted by brute-force threshold search
# on the combined 120 cases of batteries A and B; strictly increasing so every
# band is reachable).
SUM_BANDS = {
    "defect":  [(1.09, 1), (1.90, 2), (2.35, 3), (2.85, 4), (999, 5)],
    "feature": [(0.90, 1), (1.10, 2), (1.69, 3), (1.76, 4), (999, 5)],
}

# Dominance rules: the damage probe (wrong money / wrong data / privacy exposure)
# is the rubric's hard signal and must not be outvoted by the softer probes. A high
# damage reading never occurs on low-severity reports (0/18 cases in bands 1-3 on
# the batteries), so flooring on it is precision-safe.
DMG_FLOOR5 = 0.90
DMG_FLOOR4 = 0.70
REV_FLOOR5, ALL_FLOOR5 = 0.60, 0.50


def post(state, questions):
    body = json.dumps({"model": MODEL, "state": state, "questions": questions}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["answers"]


def score(flow, state):
    branch = TRIAGE_PROBES[flow]
    keys = PROBES[flow]
    qs = {k: {"type": "noul", "instructions": branch[k]} for k in keys}
    ans = post(state, qs)
    perq = {k: (1.0 - float(ans[k]["noul"])) if k in TRIAGE_INVERTED else float(ans[k]["noul"]) for k in keys}
    total = sum(perq.values())
    band = 5
    for ceiling, b in SUM_BANDS[flow]:
        if total <= ceiling:
            band = b
            break
    band = apply_rules(flow, perq, band)
    return band, perq, total


def apply_rules(flow, perq, band):
    """Damage-dominance floors (see SUM_BANDS comment)."""
    if flow == "defect":
        if perq["dmg"] >= DMG_FLOOR5:
            return max(band, 5)
        if perq["dmg"] >= DMG_FLOOR4:
            return max(band, 4)
    else:
        if perq["rev"] >= REV_FLOOR5 and perq["all"] >= ALL_FLOOR5:
            return max(band, 5)
    return band


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
    n_probes = len(PROBES[flow])
    print("triage score    %d/5   [flow: %s, sum of %d probes: %.2f/%d]" % (band, label, n_probes, total, n_probes))
    for k in PROBES[flow]:
        print("  %.2f  %s" % (perq[k], k))


if __name__ == "__main__":
    main()
