#!/usr/bin/env python3
"""Run all three batteries (A, B, C) through the 4 TRIAGE_PROBES, saving each
answer's confidence as well. Output feeds the two-stage evaluation.
Writes battery_conf.json.
"""
import json, time, urllib.request, os

BASE = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:11435/api/decide"
MODEL = "von"
OUT = os.path.join(BASE, "battery_conf.json")

from von_battery import CASES as CASES_A
from battery_b import CASES as CASES_B
from battery_c import CASES as CASES_C
from von_branches import TRIAGE_PROBES, TRIAGE_INVERTED


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
            keys = list(TRIAGE_PROBES[flow].keys())
            qs = {k: {"type": "noul", "instructions": TRIAGE_PROBES[flow][k]} for k in keys}
            t = time.time()
            ans = post(text, qs)
            probs = {k: (1.0 - float(ans[k]["noul"])) if k in TRIAGE_INVERTED else float(ans[k]["noul"]) for k in keys}
            confs = {k: float(ans[k].get("confidence", 0.0)) for k in keys}
            total = sum(probs.values())
            results.append({"battery": bname, "name": name, "want": want, "flow": flow,
                            "probs": probs, "confs": confs, "total": total})
            print(f"[{bname} {i+1}/{len(cases)}] {name:32} want{want} sum={total:.2f} conf={min(confs.values()):.2f} ({time.time()-t:.2f}s)", flush=True)
    with open(OUT, "w") as f:
        json.dump(results, f)
    print(f"\nDONE {len(results)} cases in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
