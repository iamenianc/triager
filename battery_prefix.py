#!/usr/bin/env python3
"""Test prefacing every probe with a goal statement, two variants:
  V1 per-flow : "Your goal is to accurately triage user bug reports." (defect)
                "Your goal is to accurately triage feature requests." (feature)
  V2 combined : "Your goal is to accurately triage user bug reports / feature requests."
Long probes kept verbatim. Cuts refit on A+B, C evaluated as holdout.
"""
import json, time, urllib.request, os

BASE = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:11435/api/decide"
MODEL = "von"

from von_battery import CASES as CASES_A
from battery_b import CASES as CASES_B
from battery_c import CASES as CASES_C
from von_branches import TRIAGE_PROBES

PREFIX_V1 = {"defect": "Your goal is to accurately triage user bug reports. ",
             "feature": "Your goal is to accurately triage feature requests. "}
PREFIX_V2 = "Your goal is to accurately triage user bug reports / feature requests. "


def post(state, qs):
    body = json.dumps({"model": MODEL, "state": state, "questions": qs}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["answers"]


def band_of(v, cuts):
    return 1 if v <= cuts[0] else 2 if v <= cuts[1] else 3 if v <= cuts[2] else 4 if v <= cuts[3] else 5


def refit(sub):
    vals = sorted(set(round(r["total"], 3) for r in sub))
    mids = sorted(set(round((vals[i] + vals[i+1]) / 2, 3) for i in range(len(vals)-1)))
    best = None
    for c1 in mids:
        for c2 in [m for m in mids if m > c1]:
            for c3 in [m for m in mids if m > c2]:
                for c4 in [m for m in mids if m > c3]:
                    got = [band_of(r["total"], (c1, c2, c3, c4)) for r in sub]
                    ex = sum(1 for r, g in zip(sub, got) if g == r["want"])
                    wi = sum(1 for r, g in zip(sub, got) if abs(g - r["want"]) <= 1)
                    if best is None or (ex, wi) > (best[0][0], best[0][1]):
                        best = ((ex, wi), (c1, c2, c3, c4))
    assert best is not None
    return best


def flow_of(name):
    return "defect" if name.startswith(("d", "bd", "cd", "bs01", "bs02", "cs01", "cs02", "s01", "s02")) else "feature"


def run_variant(variant):
    batteries = [("A", CASES_A), ("B", CASES_B), ("C", CASES_C)]
    results = []
    t0 = time.time()
    for bname, cases in batteries:
        for i, (name, want, text) in enumerate(cases):
            flow = flow_of(name)
            keys = list(TRIAGE_PROBES[flow].keys())
            pre = PREFIX_V1[flow] if variant == "V1" else PREFIX_V2
            qs = {k: {"type": "noul", "instructions": pre + TRIAGE_PROBES[flow][k]} for k in keys}
            ans = post(text, qs)
            probs = {k: float(ans[k]["noul"]) for k in keys}
            results.append({"battery": bname, "name": name, "want": want, "flow": flow,
                            "probs": probs, "total": sum(probs.values())})
    with open(os.path.join(BASE, f"battery_prefix_{variant}.json"), "w") as f:
        json.dump(results, f)
    print(f"\n== variant {variant} ({len(results)} cases, {time.time()-t0:.0f}s)")
    for flow in ("defect", "feature"):
        subab = [r for r in results if r["flow"] == flow and r["battery"] in ("A", "B")]
        (ex, wi), cuts = refit(subab)
        print(f"  {flow}: cuts {cuts} | A+B fit exact {ex}/60, within1 {wi}/60")
        for b in ("A", "B", "C"):
            s = [r for r in results if r["flow"] == flow and r["battery"] == b]
            e2 = sum(1 for r in s if band_of(r["total"], cuts) == r["want"])
            w2 = sum(1 for r in s if abs(band_of(r["total"], cuts) - r["want"]) <= 1)
            print(f"     {b}: exact {e2}/{len(s)} ({100*e2/len(s):.0f}%), within1 {w2}/{len(s)} ({100*w2/len(s):.0f}%)")


if __name__ == "__main__":
    for v in ("V1", "V2"):
        run_variant(v)
