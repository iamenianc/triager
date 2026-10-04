#!/usr/bin/env python3
"""Test LAYA on all 3 batteries with the current 4-probe triage sets and the
von-calibrated cuts. Pure model swap, no recalibration - measures whether Laya
generalizes better than von on identical questions.
Writes battery_laya.json. Run: python battery_laya.py   (~2 min)
"""
import json, time, urllib.request, os

BASE = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:11435/api/decide"
MODEL = "laya:en"
OUT = os.path.join(BASE, "battery_laya.json")

from von_battery import CASES as CASES_A
from battery_b import CASES as CASES_B
from battery_c import CASES as CASES_C
from von_branches import TRIAGE_PROBES, TRIAGE_INVERTED

CUTS = {"defect": (0.84, 1.14, 1.50, 2.27), "feature": (0.78, 1.07, 1.78, 2.65)}


def post(state, qs):
    body = json.dumps({"model": MODEL, "state": state, "questions": qs}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["answers"]


def band_of(total, cuts):
    return 1 if total <= cuts[0] else 2 if total <= cuts[1] else 3 if total <= cuts[2] else 4 if total <= cuts[3] else 5


def main():
    batteries = [("A", CASES_A), ("B", CASES_B), ("C", CASES_C)]
    results = []
    t0 = time.time()
    for bname, cases in batteries:
        for i, (name, want, text) in enumerate(cases):
            flow = "defect" if name.startswith(("d", "bd", "cd", "bs01", "bs02", "cs01", "cs02", "s01", "s02")) else "feature"
            keys = list(TRIAGE_PROBES[flow].keys())
            qs = {k: {"type": "noul", "instructions": TRIAGE_PROBES[flow][k]} for k in keys}
            t = time.time()
            ans = post(text, qs)
            probs = {k: (1.0 - float(ans[k]["noul"])) if k in TRIAGE_INVERTED else float(ans[k]["noul"]) for k in keys}
            total = sum(probs.values())
            band = band_of(total, CUTS[flow])
            results.append({"battery": bname, "name": name, "want": want, "flow": flow,
                            "probs": probs, "total": total, "band": band})
            mark = "OK " if band == want else "~ " if abs(band - want) <= 1 else "X "
            print(f"[{bname} {i+1}/{len(cases)}] {name:32} want{want} got{band} {mark} sum={total:.2f} ({time.time()-t:.2f}s)", flush=True)
    with open(OUT, "w") as f:
        json.dump(results, f)
    print(f"\nDONE {len(results)} cases in {time.time()-t0:.0f}s")
    for flow in ("defect", "feature"):
        for bname in ("A", "B", "C"):
            sub = [r for r in results if r["flow"] == flow and r["battery"] == bname]
            ex = sum(1 for r in sub if r["band"] == r["want"])
            wi = sum(1 for r in sub if abs(r["band"] - r["want"]) <= 1)
            print(f"laya {flow} {bname}: exact {ex}/{len(sub)} ({100*ex/len(sub):.0f}%), within1 {wi}/{len(sub)} ({100*wi/len(sub):.0f}%)")


if __name__ == "__main__":
    main()
