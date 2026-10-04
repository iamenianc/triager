#!/usr/bin/env python3
"""battery_b.py - 60-case test battery B: brand-new cases written terse and
non-technical, as a busy intern would submit them. Same structure as the
calibration battery in von_battery.py (31 defects incl. 2 style-stress,
29 features incl. 3 style-stress) but every case is new content.

Expected bands are triage intuitions, not labels the scorer sees.
Run:  python battery_b.py   (scores all 60 through von-triage.py, ~30 s)
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# (name, expected band, text)
CASES = [
 # ---- defects 5/5: money wrong / data lost / crashes / compliance, broad, no workaround
 ("bd01 upload crash loses form", 5, "app crashes when i upload a client photo and i lose the whole form i filled out. happens every time, everyone in the office has it"),
 ("bd02 wrong monthly price", 5, "quotes are showing the wrong monthly price, like 300 off. clients are seeing this in meetings. no way around it"),
 ("bd03 system down all morning", 5, "the whole system was down this morning, nobody could log in for an hour. happened twice this week"),
 ("bd04 saved policy wiped", 5, "i saved a policy for a client and when i came back all her info was gone. had to start over. this keeps happening"),
 ("bd05 missing legal page", 5, "the client report pdf is missing the legal page. compliance said we cant send any out until its fixed"),
 ("bd06 cash values sent out wrong", 5, "cash value numbers on saved policies are wrong, like totally wrong, and we already sent some to clients"),
 # ---- defects 4/5: advisors stuck or losing real work
 ("bd07 cant add beneficiary", 4, "cant add a second beneficiary, the screen wont let me go forward. support said call back. im blocked on 5 cases"),
 ("bd08 back button clears all", 4, "if i hit the back button it clears everything i typed. big cases take like 30 mins to redo"),
 ("bd09 printed summary cut off", 4, "the printed client summary cuts off half the table. i have to redo it in word by hand every time"),
 ("bd10 smoker rate wrong", 4, "quotes for smokers are using the wrong rate, a few came out lower than the carriers sheet. havent sent them yet"),
 ("bd11 drafts not saving", 4, "drafts arent saving. i lost 3 today, i keep a notepad open now and retype stuff"),
 ("bd12 tab switch logs me out", 4, "when i switch tabs it logs me out and i lose the quote i was on. happening to everyone since friday"),
 # ---- defects 3/5: friction, workaround exists, nothing lost
 ("bd13 export takes 2 mins", 3, "export takes like 2 mins, i just sit there waiting. annoying but i get coffee"),
 ("bd14 search finds nothing", 3, "search finds nothing half the time, i have to guess the client id instead. works eventually"),
 ("bd15 state dropdown doubled", 3, "the state list shows every state twice, its ugly but i can still pick mine"),
 ("bd16 numbers flash then fix", 3, "numbers flash wrong for a sec before it fixes itself. scared me once but its right when i send"),
 ("bd17 calendar picker tiny", 3, "the date picker is tiny and i keep clicking the wrong month, takes a few tries"),
 ("bd18 pdf misses last page", 3, "pdf export misses the last page unless i do it twice. second time always works"),
 # ---- defects 2/5: untidy, slightly harder, everything works
 ("bd19 save button grey", 2, "the save button is grey so i cant tell if it worked. it did work tho"),
 ("bd20 list oldest first", 2, "my client list shows oldest first, i have to scroll way down for new ppl"),
 ("bd21 logo stretched", 2, "the logo is stretched and looks blurry on the home page. purely looks"),
 ("bd22 no spellcheck notes", 2, "no spellcheck in the notes box, i type sloppy so i miss typos"),
 ("bd23 tooltip wrong shortcut", 2, "the tooltip shows the wrong keyboard shortcut. i just use the mouse"),
 ("bd24 two scrollbars", 2, "two scrollbars show up on the side sometimes. weird but everything scrolls fine"),
 # ---- defects 1/5: purely cosmetic
 ("bd25 app icon old", 1, "the app icon is still the old orange one, should be the new blue one. nobody cares"),
 ("bd26 tab title generic", 1, "the tab title always says Portal, cant tell my tabs apart"),
 ("bd27 help screenshots old", 1, "the help page still shows screenshots from the old version, buttons moved since"),
 ("bd28 print date confusing", 1, "the print preview shows the date as numbers like 20261004 instead of Oct 4. confusing for a sec"),
 ("bd29 footer typo", 1, "the footer says copright instead of copyright"),
 # ---- style-stress defects
 ("bs01 alarmist trivial", 1, "EMERGENCY!!! when i hit save it shows a spinner for like 2 seconds before the window closes. i thought it froze and almost filed a ticket!!! this is destroying my productivity!!!"),
 ("bs02 understated catastrophic", 5, "small thing, the monthly price calc has been doubling the rider cost on joint policies since monday. probably just a display thing. lmk when someone can peek"),
 # ---- features 5/5: revenue at risk
 ("bf01 agencies waiting on reviews", 5, "two big agencies said theyll move their book unless we can do policy reviews in the app. the deal is waiting on this"),
 ("bf02 lost book over comparisons", 5, "we lost the hendricks book last month bc we cant compare policies side by side. two more agencies are shopping. need this"),
 ("bf03 carrier endorsement gate", 5, "a carrier said theyll endorse us to all their brokers if we add their rate plans to quoting. thats like 2000 brokers"),
 ("bf04 batch quoting parity", 5, "competitors can quote 5 variations at once and we cant. big agencies keep bringing it up in contract talks"),
 ("bf05 demos lost over branding", 5, "agencies keep asking for the client portal with their own logo on it. we keep losing demos over it"),
 # ---- features 4/5: competitive need / frequent complaints
 ("bf06 quote templates", 4, "let us save a quote template so i dont retype the same client info 20x a day. several ppl asked"),
 ("bf07 client text reminders", 4, "add text message reminders to clients. agencies ask about it at every meeting and the other systems have it"),
 ("bf08 batch pdf export", 4, "i have 40 pdfs to do by hand every friday. batch export would save my whole afternoon"),
 ("bf09 mobile view", 4, "mobile version so i can pull up quotes at a clients kitchen table. brokers ask at every trade show, competitors have it"),
 ("bf10 shared case editing", 4, "let two advisors work the same case without overwriting each other. we keep losing edits on big cases"),
 ("bf11 built in e-sign", 4, "e-sign built in please. right now we email docs out and wait for stuff to come back. everyone complains"),
 # ---- features 3/5: saves real time, often requested
 ("bf12 address autofill", 3, "auto-fill the city and state from the zip code. saves like a min per quote"),
 ("bf13 favorite riders", 3, "let me star my usual riders so theyre pre-checked. i quote the same 3 every time"),
 ("bf14 dark mode pro", 3, "dark mode for late nights. a few of us who work evenings asked"),
 ("bf15 keyboard shortcuts", 3, "keyboard shortcuts for save and new quote. the fast typists would love it"),
 ("bf16 rename saved quotes", 3, "let me rename saved quotes. right now theyre all dates and i cant find anything"),
 ("bf17 export client list", 3, "export the client list to excel so i can sort it myself"),
 ("bf18 weekly case summary", 3, "a weekly email with my open cases so i dont forget follow ups"),
 # ---- features 2/5: nice-to-have
 ("bf20 profile photos", 2, "let us pick a profile picture for the team page"),
 ("bf21 pin top clients", 2, "pin my top clients to the top of the dashboard. saves a little scrolling"),
 ("bf22 color theme", 2, "let each person pick their own color theme. purely vibes"),
 ("bf23 solve tooltips", 2, "little hover notes explaining the fancy solve options. new ppl ask support sometimes"),
 ("bf24 notification prefs", 2, "let me choose email or in-app for alerts. some ppl asked"),
 # ---- features 1/5: novelty
 ("bf25 dark mode casual", 1, "dark mode would be nice for late nights. no rush, just a thought"),
 ("bf26 emoji reactions", 1, "emoji reactions on case comments would be fun"),
 ("bf27 cursor colors", 1, "let us pick a custom cursor color"),
 # ---- style-stress features
 ("bs03 vague middle", 3, "idk the flow between steps feels clunky?? agencies say the other guys feel smoother. maybe we need something but not sure what"),
 ("bs04 ambiguous mixed", 3, "quotes come out different than expected for special cases and honestly we need better tools for that whole space. fix or new feature, not sure"),
 ("bs05 angry revenue", 5, "THREE agencies this month told me theyre trialing the competitor bc we still cant do inforce reviews properly. we are losing huge books while the other guys do it instantly. build it NOW"),
]


def flow_for(name):
    if name.startswith("bd"): return "defect"
    if name.startswith("bf"): return "feature"
    return {"bs01": "defect", "bs02": "defect", "bs03": "feature", "bs04": "feature", "bs05": "feature"}[name[:4]]


def main():
    import importlib.util
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("vt", os.path.join(here, "von-triage.py"))
    vt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vt)
    t0 = time.time()
    res = []
    for name, want, text in CASES:
        flow = flow_for(name)
        band, perq, total = vt.score(flow, text)
        res.append((name, want, band, flow, total))
        mark = "OK " if band == want else "~ " if abs(band - want) <= 1 else "X "
        print(f"{name:32} want{want} got{band} {mark} sum={total:.2f}", flush=True)
    el = time.time() - t0
    for flow in ("defect", "feature"):
        sub = [r for r in res if r[3] == flow]
        ex = sum(1 for r in sub if r[1] == r[2])
        wi = sum(1 for r in sub if abs(r[1] - r[2]) <= 1)
        print(f"{flow}: exact {ex}/{len(sub)} ({100*ex/len(sub):.0f}%), within1 {wi}/{len(sub)} ({100*wi/len(sub):.0f}%)")
    print(f"two-band errors: {[(n, w, g) for n, w, g, _, _ in res if abs(w - g) >= 2]}")
    print(f"total wall time: {el:.0f}s")


if __name__ == "__main__":
    main()
