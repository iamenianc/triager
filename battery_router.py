#!/usr/bin/env python3
"""Stage-1 router data: one score-type question per case across all 3 batteries,
saving score + confidence. Writes battery_router.json.
"""
import json, time, urllib.request, os

BASE = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:11435/api/decide"
MODEL = "von"
OUT = os.path.join(BASE, "battery_router.json")

from von_battery import CASES as CASES_A
from battery_b import CASES as CASES_B
from battery_c import CASES as CASES_C

DEFECT_Q = {"sev": {"type": "score",
    "instructions": "How severe is this issue for the business? Judge only severity substance, not tone. 5 = critical (money wrong, data lost, crash, compliance exposure, broad impact, no workaround). 1 = trivial (cosmetic, no impact).",
    "criteria": ["1 - Trivial: purely cosmetic, nobody's work affected",
                 "2 - Minor: untidy or slightly harder, nothing lost or blocked",
                 "3 - Moderate: real friction or time lost, workaround exists, nothing lost",
                 "4 - Serious: advisors stuck or losing meaningful work",
                 "5 - Critical: money wrong, data lost, crash, or compliance exposure; broad impact, no workaround"]}}

FEATURE_Q = {"val": {"type": "score",
    "instructions": "How valuable is this requested capability to the business? Judge only business substance, not tone. 5 = revenue at risk (agencies or carriers withholding business, producers moving to competitors because it is missing). 1 = novelty (no workflow value).",
    "criteria": ["1 - Novelty: no workflow value",
                 "2 - Nice-to-have: a few users would enjoy it, nothing lost without it",
                 "3 - Convenience: saves real time for regular users, often requested, nothing lost without it",
                 "4 - Competitive need: competitors have it or complaints are frequent, absence visible to the market",
                 "5 - Revenue at risk: business is being withheld or lost because it is missing"]}}


def post(state, qs):
    body = json.dumps({"model": MODEL, "state": state, "questions": qs}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["answers"]


def main():
    batteries = [("A", CASES_A), ("B", CASES_B), ("C", CASES_C)]
    results = []
    t0 = time.time()
    for bname, cases in batteries:
        for i, (name, want, text) in enumerate(cases):
            flow = "defect" if name.startswith(("d", "bd", "cd", "bs01", "bs02", "cs01", "cs02", "s01", "s02")) else "feature"
            q = DEFECT_Q if flow == "defect" else FEATURE_Q
            t = time.time()
            ans = post(text, q)
            a = ans["sev"] if flow == "defect" else ans["val"]
            results.append({"battery": bname, "name": name, "want": want, "flow": flow,
                            "score": a["score"], "confidence": a.get("confidence", 0.0)})
            print(f"[{bname} {i+1}/{len(cases)}] {name:32} want{want} score={a['score']:.2f} conf={a.get('confidence', 0):.2f} ({time.time()-t:.2f}s)", flush=True)
    with open(OUT, "w") as f:
        json.dump(results, f)
    print(f"\nDONE {len(results)} cases in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
