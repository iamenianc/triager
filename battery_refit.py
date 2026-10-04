#!/usr/bin/env python3
"""Refit the per-flow band cuts against battery_raw.json and report accuracy."""
import json
from collections import Counter
from von_branches import DEFECT_INVERTED

INV = DEFECT_INVERTED
data = json.load(open(r"C:\Users\ianch\Hermes\Files\von-triage\battery_raw.json"))

SUM_BANDS = {"defect": [(5.0,1),(6.4,2),(8.8,3),(11.0,4),(999,5)],
             "feature": [(2.5,1),(4.3,2),(6.9,3),(12.0,4),(999,5)]}

def eff(flow, k, p): return (1.0 - p) if (flow == "defect" and k in INV) else p

def band(total, bands):
    for c, x in bands:
        if total <= c: return x
    return 5

def metrics(ps):
    n = len(ps)
    return (sum(1 for w,g in ps if w==g), sum(1 for w,g in ps if abs(w-g)<=1), n)

for flow in ("defect", "feature"):
    sub = [c for c in data if c["flow"] == flow]
    sums = []
    for c in sub:
        total = sum(eff(flow, k, p) for k, p in c["probs"].items())
        sums.append((c["want"], total))
    # current cuts
    cur = [(w, band(t, SUM_BANDS[flow])) for w, t in sums]
    e0, w0, n = metrics(cur)
    print(f"== {flow} ({n} cases)")
    print(f"  current cuts {SUM_BANDS[flow]}: exact {e0}/{n}, within1 {w0}/{n}")
    # brute-force best cuts (on the 0-24 float scale, one decimal grid)
    best = None
    for c1 in [x/10 for x in range(10, 241, 2)]:
        for c2 in [x/10 for x in range(int(c1*10), 241, 2)]:
            for c3 in [x/10 for x in range(int(c2*10), 241, 2)]:
                for c4 in [x/10 for x in range(int(c3*10), 241, 2)]:
                    got = [(w, band(t, [(c1,1),(c2,2),(c3,3),(c4,4),(999,5)])) for w, t in sums]
                    e, wi, _ = metrics(got)
                    if best is None or (e, wi) > (best[0][0], best[0][1]):
                        best = ((e, wi), (c1, c2, c3, c4))
    assert best is not None
    (e1, w1), cuts = best
    print(f"  best cuts    {cuts}: exact {e1}/{n}, within1 {w1}/{n}")
    if (e1, w1) > (e0, w0) or cuts != tuple(c for _, c in SUM_BANDS[flow]):
        got = [(w, band(t, [(cuts[0],1),(cuts[1],2),(cuts[2],3),(cuts[3],4),(999,5)])) for w, t in sums]
        print("  misses with best cuts:", [(c["name"], w, g) for (c, (w, g)) in zip(sub, got) if w != g])
    # distribution
    print("  sum ranges by want:", {w: (round(min(t for wt,t in sums if wt==w),2), round(max(t for wt,t in sums if wt==w),2)) for w in sorted(set(w for w,_ in sums))})
