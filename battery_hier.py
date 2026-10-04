#!/usr/bin/env python3
"""Hierarchical 3-layer decision tree with laya:en.

Layer 1 (broad): two options - real harm vs minor.
Layer 2 (branch): the layer-1 choice selects which refinement question to ask
                  (A -> C/D, B -> E/F).
Layer 3 (band pick): the original text is FLAVOURED with the layer-1 and layer-2
                  findings (appended as context) and the model picks the final
                  1-5 band from the full rubric.

No band cuts, no calibration needed - layer 3 picks the band directly.
Run: python battery_hier.py   (~3 calls/case, all 3 batteries)
"""
import json, time, urllib.request, os

BASE = os.path.dirname(os.path.abspath(__file__))
URL = "http://localhost:11435/api/decide"
MODEL = "laya:en"
OUT = os.path.join(BASE, "battery_hier.json")

from von_battery import CASES as CASES_A
from battery_b import CASES as CASES_B
from battery_c import CASES as CASES_C

# ---- defect tree ----
D_L1 = {"l1": {"type": "choice",
    "instructions": "What is the overall nature of this problem report?",
    "options": ["A: Something is broken or wrong with real consequences",
                "B: It is mostly cosmetic or a small annoyance"],
    "criteria": ["the report describes damage, loss, blocked work, crashes, or wrong figures",
                 "the report describes purely cosmetic issues, minor untidiness, or trivial friction"]}}
D_L2_A = {"l2": {"type": "choice",
    "instructions": "How bad is the damage described?",
    "options": ["C: Money, client data, saved records, or legal/compliance output is wrong, lost, or exposed",
                "D: Work is blocked, slowed, or must be redone, but nothing is lost or wrong"],
    "criteria": ["the report describes wrong money figures, lost or corrupted data, missing legal content, or system down for everyone",
                 "the report describes blocked or slowed work, forced re-entry, or broken features with no data loss"]}}
D_L2_B = {"l2": {"type": "choice",
    "instructions": "How much does this actually affect anyone's work?",
    "options": ["E: Everything still works fine; it just looks untidy or is briefly confusing",
                "F: It needs extra clicks, retries, or workarounds, but the work still gets done"],
    "criteria": ["the report describes appearance, labeling, or display issues with no work impact",
                 "the report describes slow performance, small repeated frictions, or manual detours"]}}
D_L3 = {"band": {"type": "choice",
    "instructions": "Given the findings above, which severity band does this defect report belong in?",
    "options": ["1 - Trivial: purely cosmetic, nobody's work is affected",
                "2 - Minor: untidy or slightly harder to use, nothing lost or blocked",
                "3 - Moderate: real friction, workaround exists, nothing is lost",
                "4 - Serious: advisors get stuck or lose meaningful work",
                "5 - Critical: money wrong, data lost, crash, or compliance exposure; broad impact, no workaround"],
    "criteria": ["purely cosmetic, no work impact",
                 "minor untidiness, everything works",
                 "real friction with a workaround, nothing lost",
                 "advisors blocked or losing meaningful work",
                 "critical: wrong money, lost data, crash, compliance, no workaround"]}}

# ---- feature tree ----
F_L1 = {"l1": {"type": "choice",
    "instructions": "What is the overall nature of this feature request?",
    "options": ["A: Not having this is costing the business something real",
                "B: It is a nice-to-have, novelty, or modest convenience"],
    "criteria": ["the request describes lost or at-risk clients, revenue, or competitive standing",
                 "the request describes preferences, small conveniences, or fun additions"]}}
F_L2_A = {"l2": {"type": "choice",
    "instructions": "How direct is the business cost of not having it?",
    "options": ["C: Paying clients, agencies, or carriers are withholding, leaving, or threatening to leave because it is missing",
                "D: No clients are leaving yet, but it causes significant daily friction, lost time, or visible competitive disadvantage"],
    "criteria": ["the request names clients, agencies, carriers, or contracts being lost or withheld",
                 "the request describes heavy repeated manual work, frequent complaints, or competitors having it"]}}
F_L2_B = {"l2": {"type": "choice",
    "instructions": "How much real workflow value does it have?",
    "options": ["E: It would save regular users a meaningful amount of time or clicks",
                "F: Little or no workflow value; purely preference or novelty"],
    "criteria": ["the request describes automating or simplifying a task users do regularly",
                 "the request describes customization, fun features, or things nobody needs"]}}
F_L3 = {"band": {"type": "choice",
    "instructions": "Given the findings above, which value band does this feature request belong in?",
    "options": ["1 - Novelty: no workflow value",
                "2 - Nice-to-have: a few users would enjoy it, nothing lost without it",
                "3 - Convenience: saves real time for regular users, often requested",
                "4 - Competitive need: competitors have it or complaints are frequent",
                "5 - Revenue at risk: business is being withheld or lost because it is missing"],
    "criteria": ["no workflow value",
                 "nice-to-have, nothing lost without it",
                 "saves real time for regular users",
                 "competitive need, visible in the market",
                 "revenue at risk, business lost or withheld"]}}


def post(state, qs):
    body = json.dumps({"model": MODEL, "state": state, "questions": qs}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=600))["answers"]


def ask_choice(state, qs, key):
    """returns (chosen_option_full_text, confidence, dist_by_option_text).
    The model echoes a CRITERION string; options and criteria are 1:1 in order,
    so map the chosen criterion back to its option by index."""
    a = post(state, qs)[key]
    choice = a["choice"].strip()
    opts = qs[key]["options"]
    crits = qs[key]["criteria"]
    chosen = None
    for idx, c in enumerate(crits):
        if choice == c.strip():
            chosen = opts[idx]
            break
    if chosen is None:  # fall back to argmax of distribution
        if crits and crits[0] in a.get("probabilities", {}):
            probs = a["probabilities"]
            best_i = max(range(len(crits)), key=lambda i: float(probs.get(crits[i], 0.0)))
            chosen = opts[best_i]
        else:
            chosen = choice
    dist = {opts[i]: float(a.get("probabilities", {}).get(crits[i], 0.0)) for i in range(len(opts))}
    return chosen, a.get("confidence", 0.0), dist


def run_tree(text, l1q, l2_a, l2_b, l3q):
    # layer 1
    c1, conf1, dist1 = ask_choice(text, l1q, "l1")
    branch = "A" if c1.startswith("A") else "B"
    # layer 2 (branched)
    l2q = l2_a if branch == "A" else l2_b
    c2, conf2, dist2 = ask_choice(text, l2q, "l2")
    letter2 = c2.split(":")[0].strip()
    # layer 3: flavour the state with the findings so far
    flavoured = (f"Report: {text}\n\n"
                 f"Layer 1 finding: {c1}\n"
                 f"Layer 2 finding: {c2}\n"
                 f"Use these findings to inform your judgment of the report.")
    ans = post(flavoured, l3q)["band"]
    choice3 = ans["choice"].strip()
    try:
        band = int(choice3.split(" ")[0].split("-")[0])
    except ValueError:
        band = None
        for idx, c in enumerate(l3q["band"]["criteria"], start=1):
            if choice3 == c:
                band = idx
                break
    dist3 = {opt.split(" ")[0]: float(p) for opt, p in ans.get("probabilities", {}).items()}
    return {"l1": c1, "l2": c2, "band": band,
            "conf": [conf1, conf2, ans.get("confidence", 0.0)],
            "dist3": dist3}


def main():
    batteries = [("A", CASES_A), ("B", CASES_B), ("C", CASES_C)]
    results = []
    t0 = time.time()
    for bname, cases in batteries:
        for i, (name, want, text) in enumerate(cases):
            flow = "defect" if name.startswith(("d", "bd", "cd", "bs01", "bs02", "cs01", "cs02", "s01", "s02")) else "feature"
            t = time.time()
            if flow == "defect":
                r = run_tree(text, D_L1, D_L2_A, D_L2_B, D_L3)
            else:
                r = run_tree(text, F_L1, F_L2_A, F_L2_B, F_L3)
            r.update({"battery": bname, "name": name, "want": want, "flow": flow, "call_s": time.time() - t})
            results.append(r)
            mark = "OK " if r["band"] == want else "~ " if r["band"] is not None and abs(r["band"] - want) <= 1 else "X "
            print(f"[{bname} {i+1}/{len(cases)}] {name:32} want{want} got{r['band']} {mark} L1={r['l1'][:1]} L2={r['l2'][:1]} ({time.time()-t:.2f}s)", flush=True)
    with open(OUT, "w") as f:
        json.dump(results, f)
    print(f"\nDONE {len(results)} cases in {time.time()-t0:.0f}s")
    for flow in ("defect", "feature"):
        for bname in ("A", "B", "C"):
            sub = [r for r in results if r["flow"] == flow and r["battery"] == bname]
            ex = sum(1 for r in sub if r["band"] == r["want"])
            wi = sum(1 for r in sub if r["band"] is not None and abs(r["band"] - r["want"]) <= 1)
            print(f"hier {flow} {bname}: exact {ex}/{len(sub)} ({100*ex/len(sub):.0f}%), within1 {wi}/{len(sub)} ({100*wi/len(sub):.0f}%)")


if __name__ == "__main__":
    main()
