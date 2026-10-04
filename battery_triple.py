#!/usr/bin/env python3
"""Battery harness for the 3-probe scorer: 3 noul probes per case, fresh run.
Writes battery_triple.json, evaluates the current cuts, refits cuts on the fresh
data, and reports accuracy (exact / within-1) per flow.
Run:  python battery_triple.py   (~30 s, 60 server calls)
"""
import json, time, urllib.request, os

BASE = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:11435/api/decide"
MODEL = "von"
OUT = os.path.join(BASE, "battery_triple.json")

from von_battery import CASES
from von_branches import DEFECT_QS, FEATURE_QS, DEFECT_INVERTED

PROBES = {
    "defect": ["trust_erosion", "valid_obstruct", "ledger_corr"],
    "feature": ["placement", "funding_solves", "comp_disadv"],
}
CUTS = {
    "defect": (0.33, 0.61, 0.69, 1.13),
    "feature": (0.26, 0.35, 0.87, 0.87),  # note: c3==c4 in-sample; refit below
}

def flow_for(name):
    if name.startswith("d"): return "defect"
    if name.startswith("f"): return "feature"
    return {"s01":"defect","s02":"defect","s03":"feature","s04":"feature","s05":"feature"}[name[:3]]

def post(state, qs):
    body = json.dumps({"model": MODEL, "state": state, "questions": qs}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["answers"]

if __name__ == "__main__":
    results = []
    t0 = time.time()
    for i, (name, want, text) in enumerate(CASES):
        flow = flow_for(name)
        branch = DEFECT_QS if flow == "defect" else FEATURE_QS
        inv = DEFECT_INVERTED if flow == "defect" else set()
        keys = PROBES[flow]
        qs = {k: {"type": "noul", "instructions": branch[k]} for k in keys}
        t = time.time()
        ans = post(text, qs)
        probs = {k: float(a["noul"]) for k, a in ans.items()}
        eff = {k: (1.0 - probs[k]) if k in inv else probs[k] for k in keys}
        total = sum(eff.values())
        c = CUTS[flow]
        band = 1 if total <= c[0] else 2 if total <= c[1] else 3 if total <= c[2] else 4 if total <= c[3] else 5
        results.append({"name": name, "want": want, "flow": flow, "probs": probs, "total": total, "band_fixed": band})
        print(f"[{i+1}/60] {name:32} want{want} sum={total:.2f} -> {band} {'OK ' if band==want else '~ ' if abs(band-want)<=1 else 'X '} ({time.time()-t:.2f}s)", flush=True)
    with open(OUT, "w") as f:
        json.dump(results, f)
    print(f"\nDONE {len(results)} cases in {time.time()-t0:.0f}s")

    # eval: fixed cuts vs refit on fresh data
    def band_of(total, cuts):
        return 1 if total <= cuts[0] else 2 if total <= cuts[1] else 3 if total <= cuts[2] else 4 if total <= cuts[3] else 5

    def acc(sub, cuts, key="total"):
        n = len(sub)
        ex = sum(1 for r in sub if band_of(r[key], cuts) == r["want"])
        wi = sum(1 for r in sub if abs(band_of(r[key], cuts) - r["want"]) <= 1)
        return ex, wi, n

    for flow_ in ("defect", "feature"):
        sub = [r for r in results if r["flow"] == flow_]
        ex, wi, n = acc(sub, CUTS[flow_])
        print(f"== {flow_} ({n} cases)")
        print(f"  current cuts {CUTS[flow_]}: exact {ex}/{n}, within1 {wi}/{n}")
        # refit: strictly increasing cuts from midpoints between distinct sums
        sums = sorted(set(round(r["total"], 3) for r in sub))
        mids = sorted(set(round((sums[i] + sums[i+1]) / 2, 3) for i in range(len(sums)-1)))
        best = None
        for c1 in mids:
            for c2 in [m for m in mids if m > c1]:
                for c3 in [m for m in mids if m > c2]:
                    for c4 in [m for m in mids if m > c3]:
                        e, w2, _ = acc(sub, (c1, c2, c3, c4))
                        if best is None or (e, w2) > (best[0][0], best[0][1]):
                            best = ((e, w2), (c1, c2, c3, c4))
        assert best is not None
        (e1, w1), cuts = best
        print(f"  refit cuts    {cuts}: exact {e1}/{n}, within1 {w1}/{n}")
        misses = [(r["name"], r["want"], band_of(r["total"], CUTS[flow_])) for r in sub if band_of(r["total"], CUTS[flow_]) != r["want"]]
        for m in misses:
            print("    miss:", m)
