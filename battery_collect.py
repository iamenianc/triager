#!/usr/bin/env python3
"""Run the 60-case battery once, save per-probe probabilities for scheme comparison."""
import json, sys, time, urllib.request, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from von_battery import CASES
from von_branches import DEFECT_QS, FEATURE_QS, DEFECT_INVERTED

URL = "http://localhost:11435/api/decide"
MODEL = "von"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "battery_raw.json")

def post(state, questions):
    body = json.dumps({"model": MODEL, "state": state, "questions": questions}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["answers"]

def flow_for(name):
    if name.startswith("d"): return "defect"
    if name.startswith("f"): return "feature"
    return {"s01":"defect","s02":"defect","s03":"feature","s04":"feature","s05":"feature"}[name[:3]]

results = []
if __name__ == "__main__":
    t0 = time.time()
    for i, (name, want, text) in enumerate(CASES):
        flow = flow_for(name)
        branch = DEFECT_QS if flow == "defect" else FEATURE_QS
        inverted = DEFECT_INVERTED if flow == "defect" else set()
        qs = {k: {"type": "noul", "instructions": q} for k, q in branch.items()}
        t = time.time()
        ans = post(text, qs)
        probs = {k: float(v["noul"]) for k, v in ans.items()}
        results.append({"name": name, "want": want, "flow": flow, "probs": probs})
        print(f"[{i+1}/60] {name:32} want{want} ({time.time()-t:.1f}s) total={sum(probs.values()):.2f}", flush=True)

    with open(OUT, "w") as f:
        json.dump(results, f)
    print(f"\nDONE {len(results)} cases in {time.time()-t0:.0f}s -> {OUT}")
