#!/usr/bin/env python3
"""battery_harness.py - score the 60-case battery with the live probes, fit the
per-flow band cuts (and the damage-dominance rules), and report accuracy.

The battery is both the fitting set and the only measurement we have, so the
reported accuracy is in-sample. Treat it as a calibration report, not a
generalisation estimate.

Run:  python battery_harness.py   (~1 min, 60 server calls)
"""
import json, time, urllib.request, os

BASE = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:11435/api/decide"
MODEL = "von"
OUT = os.path.join(BASE, "battery_results.json")

from battery import CASES, flow_for
from von_branches import TRIAGE_PROBES, TRIAGE_INVERTED

DMG_FLOOR5, DMG_FLOOR4, REV_FLOOR5, ALL_FLOOR5 = 0.90, 0.70, 0.50, 0.40


def apply_rules(flow, perq, band):
    if flow == "defect":
        if perq["dmg"] >= DMG_FLOOR5:
            return max(band, 5)
        if perq["dmg"] >= DMG_FLOOR4:
            return max(band, 4)
    else:
        if perq["rev"] >= REV_FLOOR5 and perq["all"] >= ALL_FLOOR5:
            return max(band, 5)
    return band


def post(state, qs):
    body = json.dumps({"model": MODEL, "state": state, "questions": qs}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["answers"]


def band_of(v, cuts):
    return 1 if v <= cuts[0] else 2 if v <= cuts[1] else 3 if v <= cuts[2] else 4 if v <= cuts[3] else 5


def refit(sub, flow):
    totals = sorted(set(round(r["total"], 3) for r in sub))
    mids = sorted(set(round((totals[i] + totals[i+1]) / 2, 3) for i in range(len(totals)-1)))
    best = None
    for c1 in mids:
        for c2 in [m for m in mids if m > c1]:
            for c3 in [m for m in mids if m > c2]:
                for c4 in [m for m in mids if m > c3]:
                    ex = wi = 0
                    for r in sub:
                        g = apply_rules(flow, r["probs"], band_of(r["total"], (c1, c2, c3, c4)))
                        ex += 1 if g == r["want"] else 0
                        wi += 1 if abs(g - r["want"]) <= 1 else 0
                    if best is None or (ex, wi) > (best[0][0], best[0][1]):
                        best = ((ex, wi), (c1, c2, c3, c4))
    assert best is not None
    return best


def main():
    results = []
    t0 = time.time()
    for i, (name, want, text) in enumerate(CASES):
        flow = flow_for(name)
        keys = list(TRIAGE_PROBES[flow].keys())
        qs = {k: {"type": "noul", "instructions": TRIAGE_PROBES[flow][k]} for k in keys}
        t = time.time()
        ans = post(text, qs)
        probs = {k: (1.0 - float(ans[k]["noul"])) if k in TRIAGE_INVERTED else float(ans[k]["noul"]) for k in keys}
        results.append({"name": name, "want": want, "flow": flow, "probs": probs, "total": sum(probs.values())})
        print(f"[{i+1}/{len(CASES)}] {name:32} want{want} sum={sum(probs.values()):.2f} ({time.time()-t:.2f}s)", flush=True)
    with open(OUT, "w") as f:
        json.dump(results, f)
    print(f"\nDONE {len(results)} cases in {time.time()-t0:.0f}s")

    for flow in ("defect", "feature"):
        sub = [r for r in results if r["flow"] == flow]
        (ex, wi), cuts = refit(sub, flow)
        print(f"\n== {flow} ({len(sub)} cases): cuts {cuts} -> exact {ex}/{len(sub)} ({100*ex/len(sub):.0f}%), within1 {wi}/{len(sub)} ({100*wi/len(sub):.0f}%)")
        for r in sub:
            g = apply_rules(flow, r["probs"], band_of(r["total"], cuts))
            mark = "OK " if g == r["want"] else "~  " if abs(g - r["want"]) <= 1 else "X  "
            print(f"   {mark} {r['name']:32} want{r['want']} got{g} sum={r['total']:.2f}")
        import statistics
        for k in TRIAGE_PROBES[flow]:
            means = {w: round(statistics.mean(r["probs"][k] for r in sub if r["want"] == w), 2)
                     for w in sorted(set(r["want"] for r in sub))}
            print(f"   probe {k}: mean by want {means}")


if __name__ == "__main__":
    main()
