#!/usr/bin/env python3
"""battery_harness.py - score the defect battery with the live probes, fit the
band cuts under an asymmetric error cost, and report accuracy.

Cuts are fitted to minimise total error cost, where over-rating severity costs
double what under-rating costs (a too-high band burns escalation capacity on
trivia; a too-low band still surfaces one band later). Ties break toward exact
hits, then within-1, then the higher band-5 cut: prefer to under-rate.

Scoring and dominance rules come from von-triage.py itself (loaded at runtime),
so the harness can never drift from production.

The battery is both the fitting set and the only measurement we have, so the
reported accuracy is in-sample. Treat it as a calibration report, not a
generalisation estimate.

Run:  python battery_harness.py   (~1 min, one server call per case)
"""
import json, time, urllib.request, os, importlib.util

BASE = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:11435/api/decide"
MODEL = "von"
OUT = os.path.join(BASE, "battery_results.json")

from battery import CASES
from von_branches import TRIAGE_PROBES, TRIAGE_INVERTED

# Load the production scorer so floors, cuts, and probes are shared, not duplicated.
_spec = importlib.util.spec_from_file_location("von_triage", os.path.join(BASE, "von-triage.py"))
von_triage = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(von_triage)

apply_rules = von_triage.apply_rules


def post(state, qs):
    body = json.dumps({"model": MODEL, "state": state, "questions": qs}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["answers"]


def band_of(v, cuts):
    return 1 if v <= cuts[0] else 2 if v <= cuts[1] else 3 if v <= cuts[2] else 4 if v <= cuts[3] else 5


# Asymmetric error cost: over-rating severity is worse than under-rating.
OVER_COST = {1: 2.0, 2: 6.0}    # scored 1 band too high / 2+ bands too high
UNDER_COST = {1: 1.0, 2: 3.0}   # scored 1 band too low / 2+ bands too low


def err_cost(got, want):
    d = got - want
    if d == 0:
        return 0.0
    return (OVER_COST if d > 0 else UNDER_COST)[min(abs(d), 2)]


def refit(sub):
    totals = sorted(set(round(r["total"], 3) for r in sub))
    mids = sorted(set(round((totals[i] + totals[i+1]) / 2, 3) for i in range(len(totals)-1)))
    best = None
    for c1 in mids:
        for c2 in [m for m in mids if m > c1]:
            for c3 in [m for m in mids if m > c2]:
                for c4 in [m for m in mids if m > c3]:
                    cost = ex = wi = 0
                    for r in sub:
                        g = apply_rules(r["probs"], band_of(r["total"], (c1, c2, c3, c4)))
                        cost += err_cost(g, r["want"])
                        ex += 1 if g == r["want"] else 0
                        wi += 1 if abs(g - r["want"]) <= 1 else 0
                    # minimise cost; ties break toward exact, within-1, then the
                    # higher band-5 cut (prefer to under-rate)
                    key = (round(cost, 6), -ex, -wi, -c4)
                    if best is None or key < best[0]:
                        best = (key, (c1, c2, c3, c4))
    assert best is not None
    return best


def main():
    results = []
    t0 = time.time()
    for i, (name, want, text) in enumerate(CASES):
        keys = von_triage.PROBES
        qs = {k: {"type": "noul", "instructions": TRIAGE_PROBES["defect"][k]} for k in keys}
        t = time.time()
        ans = post(text, qs)
        probs = {k: (1.0 - float(ans[k]["noul"])) if k in TRIAGE_INVERTED else float(ans[k]["noul"]) for k in keys}
        results.append({"name": name, "want": want, "probs": probs, "total": sum(probs.values())})
        print(f"[{i+1}/{len(CASES)}] {name:32} want{want} sum={sum(probs.values()):.2f} ({time.time()-t:.2f}s)", flush=True)
    with open(OUT, "w") as f:
        json.dump(results, f)
    print(f"\nDONE {len(results)} cases in {time.time()-t0:.0f}s")

    sub = results
    (cost, nex, nwi, _), cuts = refit(sub)
    ex, wi = -nex, -nwi
    scored = [(r, apply_rules(r["probs"], band_of(r["total"], cuts))) for r in sub]
    over = sum(1 for r, g in scored if g > r["want"])
    under = sum(1 for r, g in scored if g < r["want"])
    print(f"\n== defect ({len(sub)} cases): fitted cuts {cuts} -> exact {ex}/{len(sub)} ({100*ex/len(sub):.0f}%), within1 {wi}/{len(sub)} ({100*wi/len(sub):.0f}%), cost {cost:.1f}, over {over} / under {under}")
    prod = tuple(c for c, _ in von_triage.SUM_BANDS[:4])
    prod_cost = sum(err_cost(apply_rules(r["probs"], band_of(r["total"], prod)), r["want"]) for r in sub)
    print(f"   production cuts {prod} -> cost {prod_cost:.1f}{'  (matches fit)' if prod == cuts else '  (DIFFERS from fitted cuts)'}")
    for r, g in scored:
        mark = "OK " if g == r["want"] else "~  " if abs(g - r["want"]) <= 1 else "X  "
        print(f"   {mark} {r['name']:32} want{r['want']} got{g} sum={r['total']:.2f}")
    import statistics
    for k in von_triage.PROBES:
        means = {w: round(statistics.mean(r["probs"][k] for r in sub if r["want"] == w), 2)
                 for w in sorted(set(r["want"] for r in sub))}
        print(f"   probe {k}: mean by want {means}")


if __name__ == "__main__":
    main()
