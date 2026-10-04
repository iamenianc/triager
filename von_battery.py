"""von_battery.py - 50-case calibration battery for von-triage.py (v4 branch-router).
Varying length, type, style: defects vs features, terse vs verbose, neutral vs
alarmist vs understated, vague vs specific, angry vs polite, single vs multi-issue.
Run:  python von_battery.py   (needs von-triage.py + von_branches.py alongside)
Expected bands are triage intuitions, not labels von sees.
"""
import os, sys, subprocess, time
from collections import Counter

FILES = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, FILES)

# (name, expected band, text)
CASES = [
 # ---- T1 defects: high severity (want 5)
 ("d01 crash+data loss verbose", 5, "When importing a client CSV the application crashes with a server error on every attempt, affecting many brokers on all browsers. Entered beneficiary and quote data is lost and advisors must re-enter everything. This has blocked case submissions for two days."),
 ("d02 wrong rider calc alarmist", 5, "CRITICAL BUG!!! The quoting engine is producing COMPLETELY WRONG premium schedules for joint-life riders! Off by 8% from filed pricing tables! Brokers are FURIOUS and sending screenshots daily! This is an emergency!!!"),
 ("d03 ledger corruption terse", 5, "Cash value projections corrupted for all UL policies. Ledger rows wrong. Affects filed cases. Multiple agencies reporting."),
 ("d04 session termination epidemic", 5, "Every 10 minutes advisors are force-logged-out mid-application and lose their screen state. Since yesterday's deploy. Affects everyone, all product lines. Case managers cannot finish a single application without losing work three or four times."),
 ("d05 disclosures missing export", 5, "The exported client proposal omits the required legal disclosures section entirely. Compliance says we cannot send these documents to clients until fixed. All product lines affected. This is a regulatory exposure for every agency using the platform."),
 ("d06 calculation crash recurring", 5, "Entering a policy with an ownership change triggers a server 500 error and the quote is destroyed. Reproduced on Chrome, Edge and Firefox, 100% of attempts, four different agencies. Live meetings are being abandoned because nothing can be quoted in front of clients."),
 # ---- T1 defects: moderate-high (want 4)
 ("d07 validation blocks multi-ben", 4, "Broken validation on the insured screen prevents completing applications for cases with multiple beneficiaries. Advisors cannot advance past the screen and must call support. Affecting a growing number of brokers this week."),
 ("d08 rider costs stale tables", 4, "The quoting engine's rider cost table was not updated after the rate filing took effect. Quotes are about 3% off current filed premiums. Brokers notice occasionally when comparing with competitor illustrations."),
 ("d09 pdf export layout broken", 4, "Tables in the client proposal PDF are badly misaligned after the last release - columns overlap and the summary chart is cut off on page 3. Brokers are reformatting by hand before client meetings."),
 ("d10 field reset back button", 4, "When advisors navigate back a step on the health questions screen, all entered answers are cleared and must be re-typed. No data corruption, but long applications take twice as long. Many complaints this week."),
 ("d11 irate agency multi defects", 4, "Our largest agency reports three broken things at once: the quoting engine throws errors on specific crediting rates, saved drafts disappear when switching products, and the proposal export shows the wrong agent name. They cannot demo the platform to prospects at all."),
 ("d12 draft loss autosave", 4, "Draft applications are not autosaving. If the browser tab closes or the session times out, several screens of entered client data vanish. Support tickets are climbing and advisors are keeping paper backups, which is not a good look for an electronic application system."),
 # ---- T1 defects: moderate (want 3)
 ("d13 slow export verbose", 3, "Exporting large proposal PDFs takes 90 seconds instead of 10. No data loss, but advisors wait a long time during client meetings."),
 ("d14 intermittent freeze", 3, "The illustration screen freezes for 10-20 seconds maybe once or twice a day per advisor. Happens across browsers, more on big cases. Advisors grumble but work around it by switching tabs while it catches up."),
 ("d15 comparison feature errors", 3, "The side-by-side product comparison export occasionally shows mismatched rows when comparing more than three products. Data is right per product, just the alignment between columns drifts. Noticed by a few detail-oriented brokers."),
 ("d16 quote rounding pennies", 3, "Premium quotes round to the nearest dollar and are a few cents off from the carrier's official billing system. Not enough for clients to notice usually, but agencies doing premium finance cases flag the mismatch."),
 ("d17 ui lag during meetings", 3, "Screens take 2-3 seconds to respond to every click for the first hour each morning. Once the platform warms up it's fine. Advisors doing early client calls notice the sluggishness."),
 ("d18 email export formatting", 3, "When emailing an illustration summary directly from the platform the formatting arrives mangled in Outlook - tables collapse into plain text. Copy-paste works fine as a workaround, so most advisors are using that instead."),
 # ---- T1 defects: low-moderate (want 2)
 ("d19 button misaligned", 2, "On one screen the Save button is misaligned slightly and overlaps a label. Data entry still works fine, just looks untidy."),
 ("d20 tooltip wrong value", 2, "The tooltip on the funding solve screen shows 'IRR' where it should say 'MEIR'. A few advisors were briefly confused and asked support what it meant. Purely a labeling slip, one screen only."),
 ("d21 sort order wrong", 2, "Saved illustrations list in the order they were created instead of most-recent-first. Advisors with many saved cases scroll a while to find the latest one. No other impact."),
 ("d22 date format inconsistent", 2, "One report screen shows dates as MM/DD/YYYY while every other screen uses DD-Mon-YYYY. Occasionally causes a moment of confusion reading back-to-back screens. Nothing is calculated wrongly."),
 ("d23 help text stale", 2, "The help article linked from the quoting screen describes the old interface from two releases ago. Screenshots no longer match. Advisors following it get briefly lost before finding the right buttons."),
 ("d24 scrollbar duplicate", 2, "A cosmetic double scrollbar appears on the proposal preview pane at certain window sizes. Content scrolls fine, it just looks scrappy. One broker mentioned it in passing."),
 # ---- T1 defects: trivial (want 1)
 ("d25 typo help text", 1, "There is a typo in the help tooltip on the settings screen. It says recieve instead of receive. Cosmetic only, no functional impact."),
 ("d26 spelling logo", 1, "The footer copyright line says 'Copright' instead of 'Copyright'. Noticed during a branding review. No functional impact whatsoever."),
 ("d27 favicon old", 1, "The browser tab favicon still shows the old company logo from before the rebrand. Purely cosmetic, purely internal, nobody complains but the marketing team noticed."),
 ("d28 tab title generic", 1, "Every page's browser tab title just says 'Portal'. When advisors have six tabs open they cannot tell which is which without clicking through. Minor usability nit."),
 ("d29 pixel rounding", 1, "On very high-resolution monitors the main menu is 1 pixel wider than the design spec, making it wrap slightly differently than the mockups. Reviewed during design audit, flagged as cosmetic."),
 # ---- T2 features: high value (want 5)
 ("f01 split-dollar solves", 5, "We need advanced funding solves for split-dollar arrangements in the quoting engine. Multiple major marketing organizations report they cannot place large business with us because of this, and competitors win these cases."),
 ("f02 competitor parity econ solve", 5, "Add the economic solve method that every competitor platform has had for years. Our largest brokerage general agency says their top three producers are actively evaluating moving because we cannot model private financing cases. This is directly costing us placement."),
 ("f03 institutional integration", 5, "Two of the biggest brokerage agencies we are onboarding require SSO and automatic data sync with their agency management systems as a condition of moving their book to us. Contract negotiations are waiting on this capability."),
 ("f04 case comparison retention", 5, "Brokers are leaving for a competitor that offers inforce policy comparisons with our ledger data. Three agencies this quarter cited this feature in their offboarding surveys. We need it to stop the bleeding on renewals."),
 ("f05 carrier endorsement gate", 5, "A top-five carrier will endorse our platform to their entire field force only if we add their proprietary crediting rate modeling to the quoting engine. This endorsement would bring several thousand brokers onto the platform."),
 # ---- T2 features: moderate-high (want 4)
 ("f06 co-branding proposals", 3, "Please add co-branding to exported proposal summaries so agencies can add their own logo. Several partners have requested it and it would strengthen agency partnerships."),
 ("f07 batch quoting", 4, "Add batch quoting so a case manager can run 50 variations of a case overnight instead of one at a time. Large agencies doing case stacking would save hours per day and it would make us competitive on complex markets."),
 ("f08 e-sign integration deep", 3, "Deeper electronic signature integration: pre-fill signer data from the application and return signed documents directly into the case record. Would remove a manual handoff every case manager does dozens of times weekly."),
 ("f09 mobile advisor view", 4, "A mobile-friendly view for advisors to pull up client illustrations and quote summaries during meetings outside the office. Field brokers ask about this at every trade show; competitors have it."),
 ("f10 scenario modeling suite", 4, "Expand scenario modeling to include custom crediting rates and withdrawal schedules for advanced markets. The quoting engine covers standard cases well but advisors doing estate planning work must use external spreadsheets today."),
 # ---- T2 features: moderate (want 3)
 ("f11 csv import mapping auto", 3, "Add automatic CSV import mapping so client data imports do not require manual column matching each time. Would save case managers a few minutes per import."),
 ("f12 saved templates", 3, "Let advisors save quoting templates for their repeat case profiles so new quotes start pre-filled. Regular users mention it would save a handful of clicks per case."),
 ("f13 dark mode pro", 2, "Add a dark mode theme. Several advisors who work evenings have asked for it; it would reduce eye strain for that group. No business-critical impact but a visible quality-of-life request."),
 ("f14 dashboard customization", 3, "Allow the case manager dashboard widgets to be rearranged or hidden. Different roles want different summaries at the top. Complaints are occasional rather than frequent."),
 ("f15 export to excel raw", 3, "Add a raw-data Excel export of case tables for agencies that do their own analytics. A few larger agencies have requested it for their internal reporting."),
 ("f16 keyboard shortcuts", 3, "Add keyboard shortcuts for the most common quoting actions. Power users would move faster through repetitive entry; occasional users would not notice."),
 # ---- T2 features: low-moderate (want 2)
 ("f17 ui polish modernize", 2, "Modernize the visual design of the quoting screens - newer fonts, softer colors. The platform works well today; this would be a general freshness pass rather than fixing any workflow problem."),
 ("f18 notification prefs", 2, "Add per-user notification preferences so advisors can choose email vs in-app alerts for case status changes. A handful of users asked; default behavior would remain for everyone else."),
 ("f19 profile photos", 2, "Show profile photos in the case team view so colleagues recognize each other faster on shared cases. Nice-to-have social feature."),
 ("f20 quick help tooltips", 2, "Add hover tooltips explaining each funding solve option. New advisors ask support about these occasionally; experienced ones never look. Training-oriented nicety."),
 ("f21 recent items pin", 2, "Let users pin up to five frequently used cases to the top of the dashboard. Saves a little navigation for heavy users."),
 # ---- T2 features: trivial (want 1)
 ("f22 dark mode casual", 1, "It would be nice if the platform had a dark mode theme option for advisors working late. Purely cosmetic preference, no complaints so far."),
 ("f23 emoji reactions", 1, "Add emoji reactions to case comments for a bit of fun. Nobody has complained about communication; it would just be a lighthearted addition."),
 ("f24 custom cursor", 1, "Let users pick a custom cursor color. Pure novelty, no workflow benefit anyone has articulated."),
 ("f25 confetti celebration", 1, "Show a confetti animation when a case is submitted. Morale touch only."),
 ("f26 wallpaper gallery", 1, "Offer a small gallery of login-screen wallpapers users can pick from. Cosmetic personalization with no workflow impact."),
 # ---- style stress: alarmist / understated / vague / mixed / angry
 ("s01 alarmist trivial bug", 1, "EMERGENCY!!! CRITICAL SEVERITY 5/5: the settings page shows a spinning wheel for a second after saving before returning to the list. Advisor completely unable to function for ONE ENTIRE SECOND!!! This is destroying productivity and must be fixed immediately!!!"),
 ("s02 understated catastrophic", 5, "Minor data thing: the overnight calculation batch has been writing wrong cash values for the past week. Probably affects every inforce ledger. Might be nothing but worth a look when someone gets a chance."),
 ("s03 vague middle feature", 3, "It would be helpful if the platform were somehow smarter about how cases flow between steps. Not sure exactly what we need yet, but agencies mention friction and competitors feel smoother."),
 ("s04 ambiguous mixed", 3, "The quoting engine is fine for standard cases but for special markets the numbers come out different from what advisors expect, and honestly what we really need is better tooling for that whole space. Maybe fixes, maybe new features."),
 ("s05 angry verbose feature", 5, "This is getting ridiculous. THREE major agencies this month alone have told me they are trialing the competitor platform because we still cannot do inforce comparisons properly. Our producers are embarrassed in client meetings when they cannot answer basic questions the competitor tool answers instantly. We are losing multi-million dollar books over this while we sit on our hands. Build the comparison feature NOW."),
]

def run_py(flow, text):
    p = subprocess.run([sys.executable, os.path.join(FILES, "von-triage.py"), flow, text],
                       capture_output=True, text=True, cwd=FILES, timeout=180)
    return p.stdout.strip(), p.stderr.strip()

def flow_for(name):
    if name.startswith("d"): return "defect"
    if name.startswith("f"): return "feature"
    # style-stress: match the substance
    return {"s01":"defect","s02":"defect","s03":"feature","s04":"feature","s05":"feature"}[name[:3]]

def main():
    hits = within = 0
    times = []
    results = []
    for name, want, s in CASES:
        t = time.time()
        out, err = run_py(flow_for(name), s)
        dt = time.time() - t
        times.append(dt)
        try:
            first = out.splitlines()[0]
            band = int(first.split()[1].split("/")[0])
            total = float(first.split("probes: ")[1].split("/")[0])
            route = "T1" if "defect" in first else "T2"
            want_route = "T1" if flow_for(name) == "defect" else "T2"
        except Exception:
            print(f"{name:32} ERROR: {err[:150]}")
            continue
        ok = band == want
        hits += ok
        within += abs(band - want) <= 1
        results.append((name, want, band, total, route))
        mark = "OK " if ok else ("~  " if abs(band - want) <= 1 else "X  ")
        print(f"{name:32} want{want} got{band} {mark} sum={total:6.2f} flow={route} ({dt:.1f}s)")
    print(f"\n{hits}/{len(results)} exact, {within}/{len(results)} within 1   avg {sum(times)/len(times):.1f}s")
    print("got-band distribution: ", sorted(Counter(b for _, _, b, _, _ in results).items()))
    print("want-band distribution:", sorted(Counter(w for _, w, _, _, _ in results).items()))
    print("misses:", [(n, w, b, t) for n, w, b, t, _ in results if b != w])

if __name__ == "__main__":
    main()