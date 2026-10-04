#!/usr/bin/env python3
"""Hierarchical binary decision tree (noul only, no choice questions).

Layer 1 (broad): one yes/no question. Yes -> branch A, No -> branch B.
Layer 2 (branch): one yes/no question, chosen by the layer-1 branch.
Layer 3 (band pick): the report text is FLAVOURED with the layer-1 and layer-2
    findings (reported as facts in a preamble), then four noul probes ask the
    rubric questions directly ("Is this band-5 severe?"-style statements), and
    the argmax / sum places the band.

Run: python battery_hier2.py   (~3-4 calls/case, all 3 batteries)
"""
import json, time, urllib.request, os

BASE = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:11435/api/decide"
MODEL = "laya:en"
OUT = os.path.join(BASE, "battery_hier2.json")

from von_battery import CASES as CASES_A
from battery_b import CASES as CASES_B
from battery_c import CASES as CASES_C

# ---- defect tree (all noul) ----
D_L1 = {"l1": {"type": "noul", "instructions":
    "Does this report describe a problem with real consequences - damage, loss, blocked work, crashes, or wrong figures (rather than a cosmetic issue)?"}}
D_L2_A = {"l2": {"type": "noul", "instructions":
    "Does this report describe money, client data, saved records, or legal/compliance output being wrong, lost, exposed, or the system being completely down (rather than just blocked or slowed work)?"}}
D_L2_B = {"l2": {"type": "noul", "instructions":
    "Does this report describe extra clicks, retries, slowness, or workarounds needed to get work done (rather than something that just looks untidy or is briefly confusing)?"}}
D_L3 = [
    ("band3", "Given what the report describes, does it cause real friction that slows people down but with a workaround and nothing lost?"),
    ("band4", "Given what the report describes, does it leave advisors stuck or cost them meaningful work?"),
    ("band5", "Given what the report describes, is money wrong, data lost, the system crashed or unusable, or compliance exposed - with broad impact and no workaround?"),
    ("band1", "Given what the report describes, is it purely cosmetic with nobody's work affected?"),
]

# ---- feature tree (all noul) ----
F_L1 = {"l1": {"type": "noul", "instructions":
    "Does this request describe the business losing or risking something real by not having this (rather than a nice-to-have)?"}}
F_L2_A = {"l2": {"type": "noul", "instructions":
    "Does this report name paying clients, agencies, or carriers leaving, withholding business, or threatening to because this is missing?"}}
F_L2_B = {"l2": {"type": "noul", "instructions":
    "Does this request describe saving regular users a meaningful amount of time or clicks (rather than a preference or fun addition)?"}}
F_L3 = [
    ("band3", "Given what the request describes, would it save regular users real time and is it often requested?"),
    ("band4", "Given what the request describes, do competitors already have it or do users complain about its absence frequently?"),
    ("band5", "Given what the request describes, is business currently being lost or withheld because it is missing?"),
    ("band1", "Given what the request describes, is it a novelty with no real workflow value?"),
]


def post(state, qs):
    body = json.dumps({"model": MODEL, "state": state, "questions": qs}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["answers"]


def run_tree(text, l1q, l2a, l2b, l3):
    # layer 1
    p1 = float(post(text, l1q)["l1"]["noul"])
    branch = "A" if p1 >= 0.5 else "B"
    # layer 2 (branched on layer 1)
    l2q = l2a if branch == "A" else l2b
    p2 = float(post(text, l2q)["l2"]["noul"])
    # layer 3: flavoured state = report + the two findings as established facts
    l1_finding = ("has real consequences (damage, loss, blocked work, crashes, or wrong figures)"
                  if branch == "A" else
                  "is mostly cosmetic or a small annoyance")
    l2_finding = {
        ("A", "defect"): "involves money, data, or compliance being wrong/lost, or total outage" if p2 >= 0.5 else "involves blocked/slowed work without data loss",
        ("B", "defect"): "needs extra clicks/retries/workarounds but work gets done" if p2 >= 0.5 else "is untidy or briefly confusing with no work impact",
        ("A", "feature"): "is already costing clients, agencies, or carriers" if p2 >= 0.5 else "causes daily friction or competitive disadvantage without clients leaving",
        ("B", "feature"): "would save regular users meaningful time" if p2 >= 0.5 else "is a preference or novelty with little workflow value",
    }[(branch, "defect" if "money, client data" in l2a["l2"]["instructions"] or "carriers leaving" in l2a["l2"]["instructions"] else "feature")]
    flavoured = (f"Report: {text}\n\n"
                 f"Established finding 1: This {l1_finding}.\n"
                 f"Established finding 2: This {l2_finding}.\n"
                 f"Use these established findings when answering.")
    qs = {k: {"type": "noul", "instructions": instr} for k, instr in l3}
    ans = post(flavoured, qs)
    probs = {k: float(a["noul"]) for k, a in ans.items()}
    # band placement: high confidence on band5 -> 5; band4 -> 4; band3 -> 3; band1 -> 1; else 2
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
                         D_L3 if flow == "defect" else F_L3)
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
            print(f"binhier {flow} {bname}: exact {ex}/{len(sub)} ({100*ex/len(sub):.0f}%), within1 {wi}/{len(sub)} ({100*wi/len(sub):.0f}%)")


if __name__ == "__main__":
    main()
