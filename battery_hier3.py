#!/usr/bin/env python3
"""3-layer tree with ULTRA-SIMPLE probes: every question is 4 words or fewer.

Layer 1 (broad, 1 probe) -> Layer 2 (1 probe, branched by layer 1)
-> Layer 3 (band probes, flavoured with the two findings).

Run: python battery_hier3.py
"""
import json, time, urllib.request, os

BASE = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:11435/api/decide"
MODEL = "laya:en"
OUT = os.path.join(BASE, "battery_hier3.json")

from von_battery import CASES as CASES_A
from battery_b import CASES as CASES_B
from battery_c import CASES as CASES_C

# ---- defect tree, all probes <= 4 words ----
D_L1 = {"l1": {"type": "noul", "instructions": "Is something actually broken?"}}
D_L2_A = {"l2": {"type": "noul", "instructions": "Money or data wrong?"}}
D_L2_B = {"l2": {"type": "noul", "instructions": "Needs retries or workarounds?"}}
D_L3 = [
    ("band5", "Money lost or wrong?"),
    ("band4", "Work seriously blocked?"),
    ("band3", "Slow but workable?"),
    ("band1", "Purely cosmetic issue?"),
]

# ---- feature tree, all probes <= 4 words ----
F_L1 = {"l1": {"type": "noul", "instructions": "Losing business without it?"}}
F_L2_A = {"l2": {"type": "noul", "instructions": "Clients already leaving?"}}
F_L2_B = {"l2": {"type": "noul", "instructions": "Saves real time?"}}
F_L3 = [
    ("band5", "Business already lost?"),
    ("band4", "Competitors already have it?"),
    ("band3", "Saves daily time?"),
    ("band1", "No real value?"),
]


def post(state, qs):
    body = json.dumps({"model": MODEL, "state": state, "questions": qs}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["answers"]


def run_tree(text, l1q, l2a, l2b, l3, flow):
    p1 = float(post(text, l1q)["l1"]["noul"])
    branch = "A" if p1 >= 0.5 else "B"
    l2q = l2a if branch == "A" else l2b
    p2 = float(post(text, l2q)["l2"]["noul"])
    if flow == "defect":
        f1 = ("something is actually broken" if branch == "A" else "nothing is really broken")
        f2 = ("money or data is wrong" if (branch == "A" and p2 >= 0.5) else
              "it needs retries or workarounds" if (branch == "B" and p2 >= 0.5) else
              "it only looks untidy")
    else:
        f1 = ("business is being lost without it" if branch == "A" else "it is not costing business")
        f2 = ("clients are already leaving" if (branch == "A" and p2 >= 0.5) else
              "it saves real time" if (branch == "B" and p2 >= 0.5) else
              "it is a nice-to-have")
    flavoured = (f"Report: {text}\n\nKnown: {f1}.\nKnown: {f2}.\n")
    qs = {k: {"type": "noul", "instructions": instr} for k, instr in l3}
    ans = post(flavoured, qs)
    probs = {k: float(a["noul"]) for k, a in ans.items()}
    if probs["band5"] >= 0.5: band = 5
    elif probs["band4"] >= 0.5: band = 4
    elif probs["band3"] >= 0.5: band = 3
    elif probs["band1"] >= 0.5: band = 1
    else: band = 2
    return {"p1": p1, "p2": p2, "probs": probs, "band": band, "branch": branch}


def flow_of(name):
    return "defect" if name.startswith(("d", "bd", "cd", "bs01", "bs02", "cs01", "cs02", "s01", "s02")) else "feature"


def main():
    batteries = [("A", CASES_A), ("B", CASES_B), ("C", CASES_C)]
    results = []
    t0 = time.time()
    for bname, cases in batteries:
        for i, (name, want, text) in enumerate(cases):
            flow = flow_of(name)
            t = time.time()
            r = run_tree(text, D_L1 if flow == "defect" else F_L1,
                         D_L2_A if flow == "defect" else F_L2_A,
                         D_L2_B if flow == "defect" else F_L2_B,
                         D_L3 if flow == "defect" else F_L3, flow)
            r.update({"battery": bname, "name": name, "want": want, "flow": flow, "call_s": time.time() - t})
            results.append(r)
            mark = "OK " if r["band"] == want else "~ " if abs(r["band"] - want) <= 1 else "X "
            print(f"[{bname} {i+1}/{len(cases)}] {name:32} want{want} got{r['band']} {mark} L1={r['p1']:.2f} L2={r['p2']:.2f} ({time.time()-t:.2f}s)", flush=True)
    with open(OUT, "w") as f:
        json.dump(results, f)
    print(f"\nDONE {len(results)} cases in {time.time()-t0:.0f}s")
    for flow in ("defect", "feature"):
        for bname in ("A", "B", "C"):
            sub = [r for r in results if r["flow"] == flow and r["battery"] == bname]
            ex = sum(1 for r in sub if r["band"] == r["want"])
            wi = sum(1 for r in sub if abs(r["band"] - r["want"]) <= 1)
            print(f"simple3 {flow} {bname}: exact {ex}/{len(sub)} ({100*ex/len(sub):.0f}%), within1 {wi}/{len(sub)} ({100*wi/len(sub):.0f}%)")


if __name__ == "__main__":
    main()
