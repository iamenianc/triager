#!/usr/bin/env python3
"""battery_c.py - 60-case test battery C: brand-new scenarios mixing defect and
feature coverage from batteries A and B, but totally different subject matter.
Written in very casual conversational English, like a teenager texting.

Structure mirrors A/B: 31 defects (incl. 2 style-stress), 29 features (incl.
3 style-stress). Expected bands are triage intuitions, not labels the scorer sees.
Run:  python battery_c.py   (scores all 60 through von-triage.py, ~45 s)
"""
import os, sys, time

# (name, expected band, text)
CASES = [
 # ---- defects 5/5: money/data/compliance wreckage, everyone hit
 ("cd01 whole ledger shifted", 5, "ok so the ledger thing is like fully broken?? every policy in the saved list shows someone elses cash value and we already mailed some of these out to actual clients so yeah thats bad"),
 ("cd02 app bricked all day", 5, "the app straight up does not open anymore. like AT ALL. everyone in my team has been sitting here doing nothing since 9am and support just keeps saying 'we're looking into it'"),
 ("cd03 signature page vanished", 5, "so the legal signature page just... doesn't show up in the final pdf anymore?? like it's literally not there. compliance is gonna lose it when they find out we sent those"),
 ("cd04 deleted ppl's stuff", 5, "whatever you guys did over the weekend deleted like everyone's saved drafts. mine's gone, my manager's gone, everyone's gone. nothing is coming back"),
 ("cd05 wrong fees on invoices", 5, "the invoices are charging people the wrong fee. like WAY wrong. someone got charged double and we only found out bc they called to yell"),
 # ---- defects 4/5: blocked or redoing real work
 ("cd06 cant submit big cases", 4, "i literally cannot submit any case over like a million. the button just spins forever and then nothing happens. i've been stuck on this one case all week"),
 ("cd07 notes erase themselves", 4, "so if you type notes and then scroll down the page, the notes just disappear?? where do they GO. i've retyped the same paragraph like four times now"),
 ("cd08 calculator ignored riders", 4, "the quote math isn't including riders at all. like at all at all. so every quote i've done this week is basically fake and now i gotta redo them all"),
 ("cd09 locked out of my cases", 4, "weird one - i can see my case list but when i click one it says 'access denied'??? even tho it's MY case that i made?? support has like 5 of these now"),
 ("cd10 upload eats big files", 4, "every time i try to upload the big medical file it eats it and gives me an error at like 90%. i've tried like 6 times and lost a solid hour"),
 # ---- defects 3/5: friction, workaround exists
 ("cd11 prints sideways", 3, "the client summary prints sideways for some reason?? you have to go into printer settings and flip it every single time which is super annoying but whatever"),
 ("cd12 slow to open cases", 3, "cases take like a whole minute to open now, used to be instant. you just kind of scroll your phone while you wait lol"),
 ("cd13 search forgets filters", 3, "the search resets your filters every time you go back to the list. so if i filter by state and click something, coming back it's like nope all 4000 clients again"),
 ("cd14 pdf crops the chart", 3, "the graph on page 2 gets chopped in half in the pdf. you can still tell what it's saying mostly but it looks bad"),
 ("cd15 save needs two clicks", 3, "the save button like doesn't register the first click?? you have to click it twice basically every time. works eventually i guess"),
 # ---- defects 2/5: untidy, minor
 ("cd16 numbers rounded weird", 2, "the premium shows like 341.3333333 with a bunch of extra 3's instead of rounding to 2 decimals. doesn't affect anything it just looks unhinged"),
 ("cd17 tooltips blocked", 2, "the little help tooltips pop up under the text box instead of over it so the box covers them. you can read like half of them"),
 ("cd18 calendar starts monday", 2, "the calendar starts the week on monday instead of sunday which throws me off every single time i pick a date"),
 ("cd19 list not alphabetical", 2, "the rider list isn't alphabetical anymore?? it's like random order now so finding the one you want is a scavenger hunt"),
 ("cd20 weird font in pdf", 2, "part of the pdf is in this weird different font than the rest of the page. like it's readable it just looks off"),
 # ---- defects 1/5: purely cosmetic
 ("cd21 logo colors swapped", 1, "the logo colors are like swapped?? blue part is orange now and orange part is blue. nobody's mentioned it, just me apparently"),
 ("cd22 old copyright year", 1, "footer still says 2024 at the bottom lol"),
 ("cd23 welcome banner stale", 1, "the welcome banner still says 'new for 2025' and it's not 2025 anymore"),
 ("cd24 typo in tip", 1, "the tip of the day has a typo, it says 'recieve' instead of receive"),
 ("cd25 audit trail empty", 5, "so the audit trail is just... empty?? its not recording who did what or when and compliance is asking for it like today"),
 ("cd26 reminders mixed up clients", 4, "the reminder emails went out with the wrong clients info attached?? like client A got client B's appointment details. not like sensitive sensitive but i had to call and apologize to two ppl"),
 ("cd27 second monitor cut off", 3, "on the big monitor the window cuts off the bottom so the submit button is just GONE until you drag the whole window up. works fine on the laptop screen tho"),
 ("cd28 weekend dates allowed", 2, "the date picker lets you pick weekends for business stuff and then complains after you submit. just grey out the weekends already"),
 ("cd29 broken image thank you", 1, "the thank you page after submitting has a broken image icon in the middle of it. literally everything else is fine"),
 # ---- style-stress defects
 ("cs01 dramatic about nothing", 1, "OMG the loading spinner is PINK now??? it used to be blue?? this is literally so random, can someone fix this before i lose my mind"),
 ("cs02 casual about disaster", 5, "hey quick q - so the payment portal charged like 40 clients the wrong amount overnight. might be a display thing or might be real, can someone peek when free? thx"),
 # ---- features 5/5: revenue on the line
 ("cf01 biggest client waiting", 5, "our biggest agency literally said they're walking unless we get the automated policy review thing. like the actual biggest one. this isn't a maybe"),
 ("cf02 competitor keeps winning", 5, "we've lost like 3 agencies to the competitor this quarter bc their app can quote straight from a photo of the form and we can't. they demo it at every meeting and it looks SO good"),
 ("cf03 carrier deal blocked", 5, "the carrier deal is stuck bc we can't sync with their system. like they will not sign until that works. that's a whole entire carrier's brokers we're talking about"),
 ("cf04 churn over reports", 5, "clients keep canceling over the reporting thing. like the exit surveys all say the same line - 'switched to a platform that can generate client reports'. it's like every week someone leaves"),
 # ---- features 4/5: competitive need, loud complaints
 ("cf05 quote from phone", 4, "brokers keep asking if they can pull up quotes on their phone during meetings and the answer is just no and they make a face. the other platforms have apps apparently"),
 ("cf06 saved comparisons", 4, "can we like save a comparison?? every single time i want to compare two policies i have to rebuild the whole thing from scratch. agencies ask for this constantly"),
 ("cf07 text updates", 4, "clients want text updates when their case moves along instead of checking email. other companies do it and honestly it just seems basic at this point"),
 ("cf08 digital signatures", 4, "we're still printing things out for wet signatures in 2026?? every other platform does e-sign now. this comes up in literally every demo"),
 ("cf09 multi advisor editing", 4, "big teams need two people editing the same case at once, right now it just kicks whoever's second. larger agencies bring this up a lot"),
 # ---- features 3/5: real convenience
 ("cf10 auto save drafts", 3, "the app should just save as you type?? like every website does this now. losing your spot when the tab closes is just annoying enough to notice daily"),
 ("cf11 duplicate finder", 3, "a thing that warns you when you're about to enter a client that already exists?? i've made like 3 accidental doubles this month"),
 ("cf12 sort remembered", 3, "just let the client list REMEMBER that i sorted it, every page load it flips back to the default order and i have to redo it"),
 ("cf13 easy resend", 3, "a resend button for the client welcome email, rn you have to find the case, open settings, dig around... takes like 5 clicks for something i do a lot"),
 ("cf14 batch status change", 3, "let me select like 20 cases and mark them reviewed all at once instead of opening each one individually. takes foreeee rn"),
 ("cf15 export open cases", 3, "an export button for my open cases would honestly save me a spreadsheet session every monday"),
 # ---- features 2/5: nice to have
 ("cf16 highlight my cases", 2, "it'd be nice if my own cases showed up in a different color in the team list. just a visual thing"),
 ("cf17 quick notes widget", 2, "a little sticky notes widget on the dashboard would be cute. some ppl would use it"),
 ("cf18 sound on complete", 2, "a lil ding when a long quote finishes would be nice so i dont have to babysit it"),
 ("cf19 theme picker", 2, "let ppl pick a different color theme. some ppl at the office were talking about it"),
 ("cf20 pin favorite reports", 2, "let me pin my 2 favorite reports to the top instead of scrolling the whole report menu. would save a little time for heavy users"),
 # ---- features 1/5: novelty
 ("cf21 confetti on submit", 1, "confetti when you submit a case would just be fun lol"),
 ("cf22 profile vibes", 1, "let us pick a little avatar for the team page. purely for the vibes"),
 ("cf23 cursor trail", 1, "a sparkle cursor trail option. some ppl would think it's funny"),
 ("cf24 login background art", 1, "cool artwork on the login screen would be a nice touch. no one's asked"),
 ("cf25 attach to notes", 3, "let me attach a file to a case note?? rn you have to email it separately and honestly everyone forgets to"),
 ("cf26 print friendly dashboard", 2, "a print friendly version of the dashboard for the monday meetings. a few ppl asked for it"),
 # ---- style-stress features
 ("cs03 vague musing", 3, "idk man sometimes the whole thing just feels slow?? like not broken just kinda... sluggish?? agencies mention it sometimes. maybe we fix stuff, maybe we build stuff, not sure"),
 ("cs04 confused and mixed", 3, "so i can't tell if this is a bug or like a missing thing?? the special markets quotes come out weird and honestly we might just need better tools for that whole area idk"),
 ("cs05 furious but real", 5, "ok i'm actually done being nice about this. THREE of my agencies are trialing the other platform RIGHT NOW because we still can't do side by side comparisons. they demo it and it just works and we have NOTHING. i'm losing books i've worked on for YEARS over this. build the thing"),
]


def flow_for(name):
    if name.startswith(("cd", "cs01", "cs02")):
        return "defect"
    return "feature"


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
