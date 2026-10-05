#!/usr/bin/env python3
"""battery.py - the calibration battery: 61 cases written in a standard,
objective, unemotional, professional register by a business user (advisor,
operations or agency staff), not by the IT team.

Structure: 32 defect reports, 29 feature requests, spread across the five bands.
Expected bands are triage intuitions, not labels the scorer sees.

Run:  python battery_harness.py   (scores all 61, fits cuts, reports accuracy)
"""
import os

CASES = [
 # ---------------- defects: band 5 ----------------
 ("d01 premium differs from illustration", 5, "Premium amounts on issued contracts differ from the amounts shown in the approved illustration. Approximately 40 policies are affected and client statements have been mailed."),
 ("d02 timeout clears application", 5, "The application deletes all entered client information when the session times out. Advisors must re-enter complete applications, and this affects every user of the electronic application module."),
 ("d03 platform unavailable", 5, "The platform has been unavailable since 08:00. No users can log in and existing sessions were terminated. Case work has stopped for the entire operations team."),
 ("d04 disclosure page omitted", 5, "Exported client illustrations omit the required regulatory disclosure page. Compliance has advised that no documents may be issued until this is corrected."),
 ("d05 beneficiary records crossed", 5, "Beneficiary details saved in a case file are being replaced by those of a different client. Confirmed on 12 cases across three agencies, and incorrect records have been sent to two carriers."),
 ("d06 cash values incorrect", 5, "Cash value projections in the ledger are displayed incorrectly for all whole life products. Advisors have presented these figures in client meetings."),
 ("d07 billing amount incorrect", 5, "Monthly billing statements are charging an incorrect premium amount, in some cases double. Billing has been running incorrectly for six days."),
 # ---------------- defects: band 4 ----------------
 ("d08 cannot add beneficiaries", 4, "Multiple beneficiaries cannot be added to a case as the screen prevents progression. Advisors are unable to submit the affected applications and have escalated the matter to support."),
 ("d09 navigation clears questionnaire", 4, "Using the back navigation clears all responses entered on the health questionnaire. Applications of this type take approximately 30 additional minutes to complete."),
 ("d10 case summary truncated", 4, "The printed case summary truncates the ledger table. Advisors are reformatting the document manually before client meetings."),
 ("d11 tobacco rates outdated", 4, "Quoting results for tobacco-rated cases do not reflect the carrier rate tables published on 1 September. Quotes produced since that date require review."),
 ("d12 drafts not retained", 4, "Draft applications are not being retained. Advisors report repeated loss of entered work and have begun maintaining paper records."),
 ("d13 session ends on case switch", 4, "Switching between open cases ends the session. Work in progress on the previous case is not recoverable."),
 ("d32 claim advice fails on long fields", 4, "Under Member's Information, Claim -> Enter Disablement Date (e.g., 11/09/2026). This process will fail if one of the fields is over 255 characters long, as confirmed by Rock. Please use the 2 below members as examples: Member 644455 under Akamai Technologies Netherlands B.V. Australian Branch (Group ID 485) Member 659266 under Cloudera (Aust) Pty Ltd (Group ID 2059) Both examples have very long UW decision that is causing the whole document to fail to generate."),
 # ---------------- defects: band 3 ----------------
 ("d14 export takes two minutes", 3, "Policy illustration exports take approximately two minutes to generate. This is slower than previously observed, although the export completes."),
 ("d15 partial search fails", 3, "Client search does not return matches for partial surnames. Users must enter the full name or reference number to locate a record."),
 ("d16 duplicate state entries", 3, "The state selection list contains duplicate entries. Selection remains possible, but the list is twice its intended length."),
 ("d17 premium flashes incorrectly", 3, "Displayed premium values briefly show an incorrect figure before the page refreshes. The final value is correct."),
 ("d18 date picker unresponsive", 3, "The date picker requires several attempts to select a month. Dates remain selectable."),
 ("d19 last page omitted", 3, "PDF exports occasionally omit the final page on the first attempt. Re-exporting produces the complete document."),
 # ---------------- defects: band 2 ----------------
 ("d20 save gives no confirmation", 2, "The save action provides no visible confirmation. Records are saved correctly, but users cannot confirm this at the time."),
 ("d21 client list oldest first", 2, "The client list is ordered oldest first. Recent records require scrolling to locate."),
 ("d22 logo distorted", 2, "The company logo is distorted on the home page. Functionality is unaffected."),
 ("d23 notes not spell-checked", 2, "The notes field does not spell-check entries. Typing errors are not flagged."),
 ("d24 incorrect shortcut in tooltip", 2, "A tooltip references an incorrect keyboard shortcut. The shortcut itself operates correctly."),
 ("d25 second scrollbar appears", 2, "A second scrollbar appears on the case preview pane at certain window sizes. Content remains scrollable."),
 # ---------------- defects: band 1 ----------------
 ("d26 footer spelling error", 1, "The footer contains a spelling error: copright rather than copyright."),
 ("d27 application icon outdated", 1, "The application icon has not been updated to the current brand mark."),
 ("d28 browser tabs untitled", 1, "All browser tabs are titled Portal, so multiple open tabs cannot be distinguished."),
 ("d29 help screenshots outdated", 1, "The help article contains screenshots from an earlier release. The controls described have since moved."),
 ("d30 print date format", 1, "Print preview displays dates in numeric form such as 20261004 rather than the configured display format."),
 ("d31 welcome banner outdated", 1, "The welcome banner references the 2025 product year."),
 # ---------------- features: band 5 ----------------
 ("f01 agencies require reviews", 5, "Two national agencies have advised that they will transfer their books to a competitor unless inforce policy reviews are available. The combined annual premium is material to our targets."),
 ("f02 carrier endorsement contingent", 5, "A carrier has offered to endorse the platform to its field force, approximately 2,000 producers, conditional on support for its crediting rate models."),
 ("f03 agencies moved this quarter", 5, "Three agencies have moved to a competing platform this quarter, citing the absence of side-by-side policy comparison. Offboarding records confirm the stated reason."),
 ("f04 onboarding blocked on sync", 5, "Our largest brokerage group requires automated synchronisation with its agency management system as a condition of onboarding. The book is currently placed with another platform."),
 ("f05 renewals lost to portal", 5, "Client retention reporting shows recurring renewal losses where the competing platform's branded client portal is cited as the reason."),
 # ---------------- features: band 4 ----------------
 ("f06 quote templates requested", 4, "Advisors request reusable quote templates. Client details are currently re-entered for comparable cases, and this request is raised in most agency reviews."),
 ("f07 integrated e-signature", 4, "Electronic signature integrated with the case record is requested. The current process requires printing and manual return of signed documents; competitors provide this."),
 ("f08 batch document generation", 4, "Batch generation of client documents is requested. Approximately 40 documents are produced individually each week, and competitor platforms offer batch processing."),
 ("f09 mobile access requested", 4, "Mobile access to quotes and summaries is requested for client meetings. Competitors provide a mobile application."),
 ("f10 concurrent case editing", 4, "Two advisors require the ability to work on the same case concurrently. The current behaviour prevents the second user from saving."),
 ("f11 automated client reminders", 4, "Automated reminders for outstanding medical requirements are requested. Follow-up is currently manual and is frequently missed."),
 # ---------------- features: band 3 ----------------
 ("f12 postcode autofill", 3, "Automatic completion of city and state from the postcode is requested to reduce data entry on each quote."),
 ("f13 preferred riders", 3, "Users request that frequently used riders can be marked as preferred and pre-selected."),
 ("f14 dark theme for evenings", 3, "A dark display theme is requested by advisors who work outside standard hours."),
 ("f15 keyboard shortcuts", 3, "Keyboard shortcuts for common quote actions are requested by high-volume users."),
 ("f16 naming saved quotes", 3, "The ability to name saved quotes is requested, as current naming makes records difficult to locate."),
 ("f17 weekly case summary", 3, "A weekly summary of open cases is requested to support follow-up activity."),
 # ---------------- features: band 2 ----------------
 ("f18 team profile photographs", 2, "Display of a profile photograph on the team page is requested."),
 ("f19 pin frequent clients", 2, "Pinning frequently used clients to the top of the dashboard is requested."),
 ("f20 per-user colour themes", 2, "Per-user colour themes are requested."),
 ("f21 funding solve tooltips", 2, "Hover text explaining the funding solve options is requested for newer advisors."),
 ("f22 notification preferences", 2, "Per-user notification preferences, by email or in application, are requested."),
 ("f23 printable dashboard", 2, "A print-friendly version of the dashboard is requested for weekly meetings."),
 # ---------------- features: band 1 ----------------
 ("f24 optional dark theme", 1, "A dark display theme is suggested as a preference with no workflow impact."),
 ("f25 emoji on comments", 1, "Emoji reactions on case comments are suggested."),
 ("f26 custom cursor colours", 1, "Custom cursor colours are suggested."),
 ("f27 completion sound", 1, "An audible alert when quote generation completes is suggested."),
 ("f28 login backgrounds", 1, "A selection of login screen backgrounds is suggested."),
 ("f29 dashboard greeting", 1, "Personalisation of the dashboard greeting message is suggested."),
]


def flow_for(name):
    return "defect" if name.startswith("d") else "feature"


if __name__ == "__main__":
    from collections import Counter
    print("total:", len(CASES))
    print("defects:", sum(1 for n, _, _ in CASES if flow_for(n) == "defect"),
          "features:", sum(1 for n, _, _ in CASES if flow_for(n) == "feature"))
    print("band distribution:", sorted(Counter(w for _, w, _ in CASES).items()))
