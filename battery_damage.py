#!/usr/bin/env python3
"""Recalibrate with privacy added to the damage probe + damage-dominance rules.
Runs all 3 batteries, fits cuts on A+B, applies the rules, reports incl. holdout C.
"""
import json, time, urllib.request, os

BASE = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:11435/api/decide"
MODEL = "von"
OUT = os.path.join(BASE, "battery_damage.json")

from von_battery import CASES as CASES_A
from battery_b import CASES as CASES_B
from battery_c import CASES as CASES_C
from von_branches import TRIAGE_PROBES

# damage-dominance rules (see README): wrong money / wrong data / privacy exposure
# is the rubric's hard signal and cannot be outvoted by softer probes.
def apply_rules(flow, probs, band):
    if flow == "defect":
        if probs["dmg"] >= 0.90:
            return max(band, 5)
        if probs["dmg"] >= 0.70:
            return max(band, 4)
    else:
        if probs["rev"] >= 0.60 and probs["all"] >= 0.50:
            return max(band, 5)
    return band


def post(state, qs):
    body = json.dumps({"model": MODEL, "state": state, "questions": qs}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["answers"]


def band_of(v, cuts):
    return 1 if v <= cuts[0] else 2 if v <= cuts[1] else 3 if v <= cuts[2] else 4 if v <= cuts[3] else 5


def flow_of(name):
    return "defect" if name.startswith(("d", "bd", "cd", "bs01", "bs02", "cs01", "cs02", "s01", "s02")) else "feature"


def main():
    batteries = [("A", CASES_A), ("B", CASES_B), ("C", CASES_C)]
    results = []
    t0 = time.time()
    for bname, cases in batteries:
        for i, (name, want, text) in enumerate(cases):
            flow = flow_of(name)
            keys = list(TRIAGE_PROBES[flow].keys())
            qs = {k: {"type": "noul", "instructions": TRIAGE_PROBES[flow][k]} for k in keys}
            ans = post(text, qs)
            probs = {k: float(ans[k]["noul"]) for k in keys}
            results.append({"battery": bname, "name": name, "want": want, "flow": flow,
                            "probs": probs, "total": sum(probs.values())})
    with open(OUT, "w") as f:
        json.dump(results, f)
    print(f"DONE {len(results)} cases in {time.time()-t0:.0f}s")

    for flow in ("defect", "feature"):
        subab = [r for r in results if r["flow"] == flow and r["battery"] in ("A", "B")]
        totals = sorted(set(round(r["total"], 3) for r in subab))
        mids = sorted(set(round((totals[i] + totals[i+1]) / 2, 3) for i in range(len(totals)-1)))
        best = None
        for c1 in mids:
            for c2 in [m for m in mids if m > c1]:
                for c3 in [m for m in mids if m > c2]:
                    for c4 in [m for m in mids if m > c3]:
                        ex = wi = 0
                        for r in subab:
                            g = apply_rules(flow, r["probs"], band_of(r["total"], (c1, c2, c3, c4)))
                            ex += 1 if g == r["want"] else 0
                            wi += 1 if abs(g - r["want"]) <= 1 else 0
                        if best is None or (ex, wi) > (best[0][0], best[0][1]):
                            best = ((ex, wi), (c1, c2, c3, c4))
        assert best is not None
        (ex, wi), cuts = best
        print(f"\n== {flow}: cuts {cuts} (with rules) | A+B exact {ex}/60, within1 {wi}/60")
        for b in ("A", "B", "C"):
            s = [r for r in results if r["flow"] == flow and r["battery"] == b]
            e2 = sum(1 for r in s if apply_rules(flow, r["probs"], band_of(r["total"], cuts)) == r["want"])
            w2 = sum(1 for r in s if abs(apply_rules(flow, r["probs"], band_of(r["total"], cuts)) - r["want"]) <= 1)
            print(f"   {b}: exact {e2}/{len(s)} ({100*e2/len(s):.0f}%), within1 {w2}/{len(s)} ({100*w2/len(s):.0f}%)")


if __name__ == "__main__":
    main()
