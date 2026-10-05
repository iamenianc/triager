#!/usr/bin/env python3
"""Grid-search probe weights, fit band cuts by DP on A+B, sanity-check on C.

Cuts are found exactly for each weight vector: cases sorted by weighted sum,
5 contiguous band segments, DP maximising (exact, within-1) lexicographically.
"""
import json, itertools

V = json.load(open(r"C:\Users\ianch\Hermes\Files\von-triage\battery_prefix_V1.json"))

KEYS = {"defect": ["dmg", "block", "client_visible", "all"],
        "feature": ["rev", "time", "manual", "all"]}


def best_cuts(cases, weights):
    """cases: list of dicts with want+probs. Returns ((ex,wi), cuts) exact optimum."""
    keys = list(weights.keys())
    rows = sorted(((sum(r["probs"][k] * weights[k] for k in keys), r["want"]) for r in cases), key=lambda t: t[0])
    n = len(rows)
    # precompute counts for a segment [i, j) scored as band b
    ex_count = [[0] * (n + 1) for _ in range(6)]
    wi_count = [[0] * (n + 1) for _ in range(6)]
    for b in range(1, 6):
        for i in range(n):
            c_ex = c_wi = 0
            for j in range(i, n):
                w = rows[j][1]
                c_ex += 1 if w == b else 0
                c_wi += 1 if abs(w - b) <= 1 else 0
                ex_count[b][j + 1] = ex_count[b][i] + c_ex if False else ex_count[b][j + 1]
            # simpler: recompute prefix sums properly below
    # prefix sums of exact/within1 per band
    pex = [[0] * (n + 1) for _ in range(6)]
    pwi = [[0] * (n + 1) for _ in range(6)]
    for b in range(1, 6):
        for j in range(1, n + 1):
            w = rows[j - 1][1]
            pex[b][j] = pex[b][j - 1] + (1 if w == b else 0)
            pwi[b][j] = pwi[b][j - 1] + (1 if abs(w - b) <= 1 else 0)
    # DP: state (index, band) -> best (ex, wi) tuple, plus parent for reconstruction
    NEG = (-1, -1)
    dp = [[NEG] * 6 for _ in range(n + 1)]
    par = [[None] * 6 for _ in range(n + 1)]
    dp[0][0] = (0, 0)
    for b in range(1, 6):
        for j in range(1, n + 1):
            best = NEG
            besti = None
            for i in range(0, j):
                if dp[i][b - 1] == NEG:
                    continue
                e = pex[b][j] - pex[b][i]
                w = pwi[b][j] - pwi[b][i]
                cand = (dp[i][b - 1][0] + e, dp[i][b - 1][1] + w)
                if cand > best:
                    best = cand
                    besti = i
            dp[j][b] = best
            par[j][b] = besti
    # reconstruct boundaries
    idxs = []
    j = n
    for b in range(5, 0, -1):
        i = par[j][b]
        idxs.append((i, j))
        j = i
    idxs.reverse()
    vals = [r[0] for r in rows]
    cuts = []
    for (i, j) in idxs[:-1]:
        if j - 1 < 0 or j >= n:
            cuts.append(vals[j - 1] + 1e-6)
        else:
            cuts.append((vals[j - 1] + vals[j]) / 2)
    return dp[n][5], tuple(round(c, 3) for c in cuts)


def band_of(v, cuts):
    return 1 if v <= cuts[0] else 2 if v <= cuts[1] else 3 if v <= cuts[2] else 4 if v <= cuts[3] else 5


for flow in ("defect", "feature"):
    ks = KEYS[flow]
    subab = [r for r in V if r["flow"] == flow and r["battery"] in ("A", "B")]
    subC = [r for r in V if r["flow"] == flow and r["battery"] == "C"]
    grid = [0.5, 1, 2, 3, 4]
    results = []
    for combo in itertools.product(grid, repeat=4):
        weights = dict(zip(ks, combo))
        if weights[ks[0]] < max(combo[1:]):   # require the target probe to be the heaviest-ish
            continue
        (ex, wi), cuts = best_cuts(subab, weights)
        results.append(((ex, wi), weights, cuts))
    results.sort(key=lambda t: (-t[0][0], -t[0][1]))
    print(f"===== {flow}: top 6 weight vectors by A+B fit")
    for (ex, wi), weights, cuts in results[:6]:
        line = f"  {weights} A+B {ex}/60 ex {wi}/60 wi | C: "
        e2 = w2 = 0
        for r in subC:
            g = band_of(sum(r["probs"][k] * weights[k] for k in ks), cuts)
            e2 += 1 if g == r["want"] else 0
            w2 += 1 if abs(g - r["want"]) <= 1 else 0
        print(line + f"{e2}/31 ex {w2}/31 wi | cuts {cuts}")
    print(f"  baseline (all weights 1): ", end="")
    w1 = {k: 1 for k in ks}
    (ex, wi), cuts = best_cuts(subab, w1)
    e2 = w2 = 0
    for r in subC:
        g = band_of(sum(r["probs"][k] for k in ks), cuts)
        e2 += 1 if g == r["want"] else 0
        w2 += 1 if abs(g - r["want"]) <= 1 else 0
    print(f"A+B {ex}/60 ex {wi}/60 wi | C {e2}/31 ex {w2}/31 wi | cuts {cuts}")
