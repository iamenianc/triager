#!/usr/bin/env python3
"""Flat 4-probe von scorer with SHORT probes (<= 5 words each).

Same axes as production (damage / obstruction / client-visible / everyone;
revenue / time / manual / everyone) but minimal wording.
Recalibrates cuts on batteries A+B, evaluates C, compares to the verbose 4-probe.
Writes battery_von_short.json.
"""
import json, time, urllib.request, os

BASE = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:11435/api/decide"
MODEL = "von"
OUT = os.path.join(BASE, "battery_von_short.json")

from von_battery import CASES as CASES_A
from battery_b import CASES as CASES_B
from battery_c import CASES as CASES_C

SHORT_PROBES = {
    "defect": {
        "dmg":            "Is data or money wrong?",
        "block":          "Is work blocked or lost?",
        "client_visible": "Do clients see it?",
        "all":            "Does it affect everyone?",
    },
    "feature": {
        "rev":    "Is business being lost?",
        "time":   "Does it save real time?",
        "manual": "Done by hand today?",
        "all":    "Does everyone need it?",
    },
}


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


def main():
    batteries = [("A", CASES_A), ("B", CASES_B), ("C", CASES_C)]
    results = []
    t0 = time.time()
    for bname, cases in batteries:
        for i, (name, want, text) in enumerate(cases):
            flow = flow_of(name)
            keys = list(SHORT_PROBES[flow].keys())
            qs = {k: {"type": "noul", "instructions": SHORT_PROBES[flow][k]} for k in keys}
            t = time.time()
            ans = post(text, qs)
            probs = {k: float(ans[k]["noul"]) for k in keys}
            total = sum(probs.values())
            results.append({"battery": bname, "name": name, "want": want, "flow": flow,
                            "probs": probs, "total": total, "call_s": time.time() - t})
            print(f"[{bname} {i+1}/{len(cases)}] {name:32} want{want} sum={total:.2f} ({time.time()-t:.2f}s)", flush=True)
    with open(OUT, "w") as f:
        json.dump(results, f)
    print(f"\nDONE {len(results)} cases in {time.time()-t0:.0f}s")

    print("\n== short-probe von, cuts refit on A+B, C as holdout")
    for flow in ("defect", "feature"):
        subab = [r for r in results if r["flow"] == flow and r["battery"] in ("A", "B")]
        (ex, wi), cuts = refit(subab)
        print(f"{flow}: cuts {cuts} | A+B fit exact {ex}/60, within1 {wi}/60")
        for b in ("A", "B", "C"):
            s = [r for r in results if r["flow"] == flow and r["battery"] == b]
            e2 = sum(1 for r in s if band_of(r["total"], cuts) == r["want"])
            w2 = sum(1 for r in s if abs(band_of(r["total"], cuts) - r["want"]) <= 1)
            print(f"   {b}: exact {e2}/{len(s)} ({100*e2/len(s):.0f}%), within1 {w2}/{len(s)} ({100*w2/len(s):.0f}%)")
        # probe discrimination
        import statistics
        for k in SHORT_PROBES[flow]:
            means = {w: round(statistics.mean(r["probs"][k] for r in subab if r["want"] == w), 2)
                     for w in sorted(set(r["want"] for r in subab))}
            print(f"   probe {k}: mean by want {means}")


if __name__ == "__main__":
    main()
