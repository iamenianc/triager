#!/usr/bin/env python3
"""Battery harness for the 3-probe scorer.

Runs both test batteries (A: von_battery.CASES verbose professional style,
B: battery_b.CASES terse intern style) through the 3 TRIAGE_PROBES, evaluates the
current band cuts, refits cuts on the combined data, and reports accuracy
(exact / within-1) per battery and per flow.
Run:  python battery_triple.py   (~2 min, 120 server calls)
"""
import json, time, urllib.request, os

BASE = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:11435/api/decide"
MODEL = "von"
OUT = os.path.join(BASE, "battery_triple.json")

from von_battery import CASES as CASES_A
from battery_b import CASES as CASES_B
from von_branches import TRIAGE_PROBES, TRIAGE_INVERTED


def post(state, qs):
    body = json.dumps({"model": MODEL, "state": state, "questions": qs}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["answers"]


def band_of(total, cuts):
    return 1 if total <= cuts[0] else 2 if total <= cuts[1] else 3 if total <= cuts[2] else 4 if total <= cuts[3] else 5


def acc(sub, cuts):
    n = len(sub)
    ex = sum(1 for r in sub if band_of(r["total"], cuts) == r["want"])
    wi = sum(1 for r in sub if abs(band_of(r["total"], cuts) - r["want"]) <= 1)
    return ex, wi, n


def refit(sub):
    """strictly increasing cuts from midpoints between distinct sums"""
    sums = sorted(set(round(r["total"], 3) for r in sub))
    mids = sorted(set(round((sums[i] + sums[i+1]) / 2, 3) for i in range(len(sums)-1)))
    best = None
    for c1 in mids:
        for c2 in [m for m in mids if m > c1]:
            for c3 in [m for m in mids if m > c2]:
                for c4 in [m for m in mids if m > c3]:
                    e, wi, _ = acc(sub, (c1, c2, c3, c4))
                    if best is None or (e, wi) > (best[0][0], best[0][1]):
                        best = ((e, wi), (c1, c2, c3, c4))
    assert best is not None
    return best


def main():
    batteries = [("A", CASES_A), ("B", CASES_B)]
    results = []
    t0 = time.time()
    for bname, cases in batteries:
        for i, (name, want, text) in enumerate(cases):
            DEFECT_PREFIXES = ("d", "bd", "bs01", "bs02", "s01", "s02")
            flow = "defect" if name.startswith(DEFECT_PREFIXES) else "feature"
            keys = list(TRIAGE_PROBES[flow].keys())
            qs = {k: {"type": "noul", "instructions": TRIAGE_PROBES[flow][k]} for k in keys}
            t = time.time()
            ans = post(text, qs)
            perq = {k: (1.0 - float(ans[k]["noul"])) if k in TRIAGE_INVERTED else float(ans[k]["noul"]) for k in keys}
            total = sum(perq.values())
            results.append({"battery": bname, "name": name, "want": want, "flow": flow,
                            "probs": perq, "total": total})
            print(f"[{bname} {i+1}/{len(cases)}] {name:32} want{want} sum={total:.2f} ({time.time()-t:.2f}s)", flush=True)
    with open(OUT, "w") as f:
        json.dump(results, f)
    print(f"\nDONE {len(results)} cases in {time.time()-t0:.0f}s")

    for flow in ("defect", "feature"):
        print(f"== {flow}")
        for bname in ("A", "B"):
            sub = [r for r in results if r["flow"] == flow and r["battery"] == bname]
            ex, wi, n = acc(sub, refit(sub)[1])  # per-battery best achievable
            print(f"  battery {bname} ({n} cases): best-fit exact {ex}/{n}, within1 {wi}/{n}")
        comb = [r for r in results if r["flow"] == flow]
        (ex, wi), cuts = refit(comb)
        print(f"  COMBINED refit cuts {cuts}: exact {ex}/{len(comb)}, within1 {wi}/{len(comb)}")
        for bname in ("A", "B"):
            sub = [r for r in results if r["flow"] == flow and r["battery"] == bname]
            e2, w2, n2 = acc(sub, cuts)
            print(f"    battery {bname} with combined cuts: exact {e2}/{n2}, within1 {w2}/{n2}")
        misses = [(r["battery"], r["name"], r["want"], band_of(r["total"], cuts)) for r in comb if band_of(r["total"], cuts) != r["want"]]
        for m in misses:
            print("    miss:", m)


if __name__ == "__main__":
    main()
