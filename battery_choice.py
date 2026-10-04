#!/usr/bin/env python3
"""Choice-question framing: LAYA picks the severity band directly (one choice
question per case, rubric bands as options), across all 3 batteries.
Writes battery_choice.json. Run: python battery_choice.py   (~1 min)
"""
import json, time, urllib.request, os

BASE = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:11435/api/decide"
MODEL = "laya:en"
OUT = os.path.join(BASE, "battery_choice.json")

from von_battery import CASES as CASES_A
from battery_b import CASES as CASES_B
from battery_c import CASES as CASES_C

DEFECT_Q = {"band": {"type": "choice",
    "instructions": "Which severity band does this defect report belong in?",
    "options": [
        "1 - Trivial: purely cosmetic, nobody's work is affected",
        "2 - Minor: untidy or slightly harder to use, nothing lost or blocked",
        "3 - Moderate: real friction, workaround exists, nothing is lost",
        "4 - Serious: advisors get stuck or lose meaningful work",
        "5 - Critical: money wrong, data lost, crash, or compliance exposure; broad impact, no workaround"],
    "criteria": [
        "the report describes purely cosmetic damage with no work impact",
        "the report describes minor untidiness with everything still working",
        "the report describes real friction with a workaround and nothing lost",
        "the report describes advisors blocked or losing meaningful work",
        "the report describes critical damage: wrong money, lost data, crash, compliance exposure, no workaround"]}}

FEATURE_Q = {"band": {"type": "choice",
    "instructions": "Which value band does this feature request belong in?",
    "options": [
        "1 - Novelty: no workflow value",
        "2 - Nice-to-have: a few users would enjoy it, nothing lost without it",
        "3 - Convenience: saves real time for regular users, often requested",
        "4 - Competitive need: competitors have it or complaints are frequent",
        "5 - Revenue at risk: business is being withheld or lost because it is missing"],
    "criteria": [
        "the request describes a novelty with no workflow value",
        "the request describes a nice-to-have with nothing lost without it",
        "the request describes a convenience saving real time for regular users",
        "the request describes a competitive need visible in the market",
        "the request describes revenue at risk: business withheld or lost because it is missing"]}}


def post(state, qs):
    body = json.dumps({"model": MODEL, "state": state, "questions": qs}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["answers"]


def main():
    batteries = [("A", CASES_A), ("B", CASES_B), ("C", CASES_C)]
    results = []
    t0 = time.time()
    for bname, cases in batteries:
        for i, (name, want, text) in enumerate(cases):
            flow = "defect" if name.startswith(("d", "bd", "cd", "bs01", "bs02", "cs01", "cs02", "s01", "s02")) else "feature"
            q = DEFECT_Q if flow == "defect" else FEATURE_Q
            t = time.time()
            ans = post(text, q)
            a = ans["band"]
            # the model echoes a CRITERION string; criteria are listed in the
            # same 1..5 order as the options, so index position = band number
            crits = q["band"]["criteria"]
            choice_text = a["choice"]
            band = None
            for idx, c in enumerate(crits, start=1):
                if choice_text.strip() == c:
                    band = idx
                    break
            probs = a.get("probabilities", {})
            # probability distribution keyed by criterion strings
            dist = {}
            for idx, c in enumerate(crits, start=1):
                if c in probs:
                    dist[idx] = float(probs[c])
            top = max(dist, key=dist.get) if dist else None
            if band is None and top is not None:
                band = top  # fall back to argmax of distribution
            conf = a.get("confidence", 0.0)
            results.append({"battery": bname, "name": name, "want": want, "flow": flow,
                            "band": band, "top_prob": dist.get(band, 0.0),
                            "top_prob_overall": dist.get(top, 0.0) if top else 0.0,
                            "confidence": conf, "dist": dist,
                            "call_s": time.time() - t})
            mark = "OK " if band == want else "~ " if band is not None and abs(band - want) <= 1 else "X "
            print(f"[{bname} {i+1}/{len(cases)}] {name:32} want{want} got{band} {mark} p={dist.get(band,0):.2f} conf={conf:.2f} ({time.time()-t:.2f}s)", flush=True)
    with open(OUT, "w") as f:
        json.dump(results, f)
    print(f"\nDONE {len(results)} cases in {time.time()-t0:.0f}s")
    for flow in ("defect", "feature"):
        for bname in ("A", "B", "C"):
            sub = [r for r in results if r["flow"] == flow and r["battery"] == bname]
            ex = sum(1 for r in sub if r["band"] == r["want"])
            wi = sum(1 for r in sub if r["band"] is not None and abs(r["band"] - r["want"]) <= 1)
            print(f"choice {flow} {bname}: exact {ex}/{len(sub)} ({100*ex/len(sub):.0f}%), within1 {wi}/{len(sub)} ({100*wi/len(sub):.0f}%)")


if __name__ == "__main__":
    main()
