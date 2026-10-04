import json
R = json.load(open(r"C:\Users\ianch\Hermes\Files\von-triage\battery_router.json"))
C = json.load(open(r"C:\Users\ianch\Hermes\Files\von-triage\battery_conf.json"))
conf_by_name = {r["name"]: r["confs"] for r in C}
prob_by_name = {r["name"]: r["probs"] for r in C}

def band_of(v, cuts):
    return 1 if v <= cuts[0] else 2 if v <= cuts[1] else 3 if v <= cuts[2] else 4 if v <= cuts[3] else 5

def refit(sub, valfn):
    vals = sorted(set(round(valfn(r), 3) for r in sub))
    mids = sorted(set(round((vals[i] + vals[i+1])/2, 3) for i in range(len(vals)-1)))
    best = None
    for c1 in mids:
        for c2 in [m for m in mids if m > c1]:
            for c3 in [m for m in mids if m > c2]:
                for c4 in [m for m in mids if m > c3]:
                    ex = sum(1 for r in sub if band_of(valfn(r), (c1,c2,c3,c4)) == r["want"])
                    wi = sum(1 for r in sub if abs(band_of(valfn(r), (c1,c2,c3,c4)) - r["want"]) <= 1)
                    if best is None or (ex, wi) > (best[0][0], best[0][1]):
                        best = ((ex, wi), (c1, c2, c3, c4))
    assert best is not None
    return best

# ---- stage1-only cuts (fit on A+B; C stays holdout)
for flow in ("defect", "feature"):
    sub = [r for r in R if r["flow"] == flow and r["battery"] in ("A", "B")]
    (ex, wi), cuts = refit(sub, lambda r: r["score"])
    print(f"== stage1-only {flow}: cuts {cuts} | A+B fit exact {ex}/60, within1 {wi}/60")
    for b in ("A", "B", "C"):
        s2 = [r for r in R if r["flow"] == flow and r["battery"] == b]
        e2 = sum(1 for r in s2 if band_of(r["score"], cuts) == r["want"])
        w2 = sum(1 for r in s2 if abs(band_of(r["score"], cuts) - r["want"]) <= 1)
        print(f"   {b}: exact {e2}/{len(s2)} ({100*e2/len(s2):.0f}%), within1 {w2}/{len(s2)} ({100*w2/len(s2):.0f}%)")

# ---- confidence analysis: is low-conf correlated with stage1 error?
print("\n== confidence vs stage1 error (A+B+C, combined cuts from A+B fit above)")
for flow in ("defect", "feature"):
    sub = [r for r in R if r["flow"] == flow and r["battery"] in ("A", "B")]
    _, cuts = refit(sub, lambda r: r["score"])
    allf = [r for r in R if r["flow"] == flow]
    errs = [r for r in allf if band_of(r["score"], cuts) != r["want"]]
    oks = [r for r in allf if band_of(r["score"], cuts) == r["want"]]
    import statistics
    if errs and oks:
        me = statistics.mean(r["confidence"] for r in errs)
        mo = statistics.mean(r["confidence"] for r in oks)
        print(f"  {flow}: mean conf on ERRORS {me:.3f} vs CORRECT {mo:.3f} (errs={len(errs)}, oks={len(oks)})")

# ---- hybrid: gate on confidence, escalate to 4-probe stage (cuts refit on A+B for fallback)
print("\n== hybrid (gate -> escalate to 4-probe specialist)")
for flow in ("defect", "feature"):
    subab = [r for r in R if r["flow"] == flow and r["battery"] in ("A", "B")]
    _, cuts1 = refit(subab, lambda r: r["score"])
    confs_ab = [r["confidence"] for r in subab]
    best = None
    for gate in [x/100 for x in range(10, 96, 1)]:
        tot = orr = wi = 0
        for r in R:
            if r["flow"] != flow: continue
            if r["confidence"] >= gate:
                got = band_of(r["score"], cuts1); tot += 1
            else:
                p = prob_by_name[r["name"]]
                t2 = sum(p.values())
                # fallback cuts: refit per gate is heavy; use current prod cuts (0-4) from von-triage
                PROD = {"defect": (0.84,1.14,1.50,2.27), "feature": (0.78,1.07,1.78,2.65)}[flow]
                got = band_of(t2, PROD); tot += 1
            orr += 1 if got == r["want"] else 0
            wi += 1 if abs(got - r["want"]) <= 1 else 0
        n = tot
        if best is None or (orr, wi) > (best[0][0], best[0][1]):
            best = ((orr, wi), gate)
    (orr, wi), gate = best
    n = sum(1 for r in R if r["flow"] == flow)
    esc = sum(1 for r in R if r["flow"] == flow and r["confidence"] < gate)
    print(f"  {flow}: best gate {gate:.2f} -> exact {orr}/{n} ({100*orr/n:.0f}%), within1 {wi}/{n} ({100*wi/n:.0f}%), escalated {esc}/{n} ({100*esc/n:.0f}%)")
