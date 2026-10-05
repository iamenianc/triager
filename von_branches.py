"""Branch question sets for the insurance-platform triage scorer (von-triage.py v6).
Ian's revised set: factual yes/no probes (noul), each scored by von as a float 0-1.
No rounding anywhere: probabilities are summed as floats.

Two probes are REVERSED POLARITY (yes = good = less severe) and are summed as (1 - p):
  - DEFECT  meeting_wa   (advisor can bypass during a live client meeting)
  - DEFECT  self_resolve (advisor can fix it without contacting support)
Everything else is direct polarity (yes = more severe / more valuable).

Keep key order stable: von is option-order sensitive.
"""

RUBRIC = ["no", "yes"]  # noul probes are binary; kept for reference only

# ---- 4-probe triage sets (von-triage.py) ----
# Each probe covers one axis of the severity rubric and is prefaced with the
# flow's goal statement (steadies von across writing styles; the wording of the
# question itself is load-bearing - von scores options at [MASK], so the probe
# text IS the context it reasons over. Do not shorten probes.)
# defect: damage / obstruction / client-facing stakes / universality.
DEFECT_GOAL = "Your goal is to accurately triage user bug reports. "

TRIAGE_PROBES = {
    "defect": {
        "dmg":            DEFECT_GOAL + "Does this problem destroy, corrupt, or miscalculate any client data, saved records, or money figures, or expose private client information?",
        "block":          DEFECT_GOAL + "Does this problem stop someone from finishing their work, or force them to redo work they already did?",
        "client_visible": DEFECT_GOAL + "Does this problem happen in front of a client, or affect documents or figures that clients see?",
        "all":            DEFECT_GOAL + "Does this issue meaningfully impact 100 percent of the entire user base of the software?",
    },
}
TRIAGE_INVERTED = set()  # no reversed-polarity probes in the current sets

DEFECT_QS = {
    # Group 1: System Stability
    "crash_freq": "Does this defect cause the application to crash, freeze, or return server errors during active use?",
    "session_term": "Does this failure terminate an active session and force a page reload or re-login?",
    "exec_block": "Does the system completely freeze or refuse to process the requested action?",
    # Group 2: Form Validation
    "valid_obstruct": "Do broken validation rules prevent users from completing electronic application screens?",
    "resp_disrupt": "Do unresponsive buttons, misaligned menus, or resetting fields disrupt data entry?",
    "progress_friction": "Does this defect prevent an advisor from advancing past the affected screen?",
    # Group 3: Calculations
    "actuarial_dev": "Is there a discrepancy between calculation engine outputs and filed pricing tables?",
    "ledger_corr": "Does this defect distort projected values such as cash value or internal rate of return?",
    "quote_inacc": "Does the engine produce calculation errors in premium schedules or rider costs?",
    # Group 4: Document Generation
    "layout_dist": "Does this bug misalign or cut off tables and charts in exported client documents?",
    "doc_complete": "Does the exported report omit required ledger rows or legal disclosures?",
    "render_quality": "Is the exported client document visually unreadable or unusable?",
    # Group 5: Data Retention
    "data_loss": "Does this defect erase entered client information, beneficiaries, or quote details?",
    "nav_retention": "Does the system lose entered data when switching tabs or navigating back?",
    "reentry": "Does this defect force users to manually re-enter lost draft records?",
    # Group 6: Workaround Feasibility
    "meeting_wa": "Can an advisor bypass this issue during a live client meeting?",
    "self_resolve": "Can an advisor resolve this issue without contacting technical support?",
    "detour": "Does working around this defect require a complex or time-consuming operational detour?",
    # Group 7: Defect Scope
    "broker_exposure": "Does this defect affect a broad population of active brokers and agencies?",
    "cross_product": "Does this defect impact multiple life insurance product lines?",
    "reproducibility": "Does this bug occur consistently across different operating systems and web browsers?",
    # Group 8: Client Risk
    "credibility": "Does this defect harm the advisor professional credibility in front of clients?",
    "trust_erosion": "Does this error undermine advisor confidence when working on high-value cases?",
    "presentation_exposure": "Is this bug visible during live presentations or screen shares?",
}

# reversed polarity: high probability means LESS severe -> contributes (1 - p) to the sum
DEFECT_INVERTED = {"meeting_wa", "self_resolve"}
