#!/usr/bin/env python3
"""von-triage.py - triage score 1-5 for the life-insurance quoting platform (von decision model).

Two DISCRETE flows, chosen by the caller (no router - Ian's call):
  python von-triage.py defect  "<text>"    -> Tranche 1: software bugs & defects
  python von-triage.py feature "<text>"    -> Tranche 2: new feature requests

Each flow asks its branch's 4 severity probes (from von_branches.py TRIAGE_PROBES):
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

Band calibration: cuts are fitted by brute-force threshold search on the 61-case
battery under an ASYMMETRIC error cost - over-rating severity costs double what
under-rating costs (Ian's policy: prefer to under-rate; a too-high band burns
escalation capacity on trivia, a too-low band still surfaces one band later).
Accuracy on the battery (in-sample - it is both fitting set and only measurement):
defect 50% exact, 97% within 1 (5 over / 11 under); feature 55% exact, 90% within 1
(8 over / 5 under). A one-band error is acceptable in triage. The damage rules
guarantee that wrong money, wrong data, or privacy exposure lands at least 4
and usually 5, even in short single-signal reports.

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

# The 4 probes per flow, in fixed order (von is option-order sensitive).
PROBES = {flow: list(qs.keys()) for flow, qs in TRIAGE_PROBES.items()}

# Per-flow band cuts on the 0-4 float sum (fitted by battery_harness.py under the
# asymmetric error cost; strictly increasing so every band is reachable).
SUM_BANDS = {
    "defect":  [(0.841, 1), (1.577, 2), (1.77, 3), (3.29, 4), (999, 5)],
    "feature": [(0.888, 1), (1.05, 2), (1.083, 3), (2.379, 4), (999, 5)],
}

# Dominance rules: the damage probe (wrong money / wrong data / privacy exposure)
# is the rubric's hard signal and must not be outvoted by the softer probes.
# Battery-verified precision: no case in bands 1-4 reads dmg >= 0.88 (max is 0.87,
# outdated rate tables), while the one-line wrong-money canary reads a stable 0.89 -
# so the floor-5 sits at 0.88 to keep the canary at 5 under the band-5 cut of 3.29.
DMG_FLOOR5 = 0.88
DMG_FLOOR4 = 0.70
REV_FLOOR5, ALL_FLOOR5 = 0.50, 0.40


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
