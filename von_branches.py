"""Branch question sets for the insurance-platform triage scorer (von-score.py v6).
Ian's revised set: factual yes/no probes (noul), each scored by von as a float 0-1.
No rounding anywhere: probabilities are summed as floats.

Two probes are REVERSED POLARITY (yes = good = less severe) and are summed as (1 - p):
  - DEFECT  meeting_wa   (advisor can bypass during a live client meeting)
  - DEFECT  self_resolve (advisor can fix it without contacting support)
Everything else is direct polarity (yes = more severe / more valuable).

Keep key order stable: von is option-order sensitive.
"""

RUBRIC = ["no", "yes"]  # noul probes are binary; kept for reference only

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

FEATURE_QS = {
    # Group 1: Workflow Efficiency
    "input_reduce": "Will this enhancement reduce clicks, keystrokes, and redundant data entry?",
    "turnaround": "Will this automation materially shorten case preparation and submission time?",
    "bottleneck": "Does this change eliminate a repetitive navigation hurdle in daily work?",
    # Group 2: Custom Reporting
    "proposal_clarity": "Does this feature improve the visual readability of complex policy ledgers?",
    "cobrand": "Does this expand the ability to customize and co-brand illustration summaries?",
    "comparison": "Does this export feature enable side-by-side product comparisons?",
    # Group 3: Scenario Modeling
    "funding_solves": "Does this expand modeling capabilities for concepts like split-dollar funding?",
    "actuarial_depth": "Does this add solving calculations that are currently missing from the quoting engine?",
    "projection_custom": "Does this enable custom crediting rate stress tests and withdrawal schedules?",
    # Group 4: Interface Usability
    "cognitive_load": "Will this redesign reduce user confusion and training requirements?",
    "discoverability": "Does this update make nested tools, riders, and modules easier to find?",
    "ergonomics": "Does this update noticeably improve the daily speed and feel of the platform?",
    # Group 5: System Integration
    "agency_sync": "Does this feature enable direct data synchronization with external agency management systems?",
    "handoff": "Does this eliminate manual handoffs to electronic signature or medical record tools?",
    "import_export": "Does this automate data imports and exports to remove manual re-entry?",
    # Group 6: Competitive Parity
    "feature_parity": "Is this capability required to match standard features in competitor portals?",
    "standard_gap": "Is the absence of this feature generating frequent broker complaints?",
    "comp_disadv": "Does competitor support for this capability currently cause lost business?",
    # Group 7: User Adoption
    "user_reach": "Will a majority of active brokers regularly use this feature?",
    "multiline": "Does this feature apply across multiple life insurance product lines?",
    "volume": "Will this feature be used in a substantial portion of monthly quotes or applications?",
    # Group 8: Commercial Growth
    "large_case": "Does this feature directly help brokers design and close larger cases?",
    "distribution": "Does this capability improve leverage in distribution negotiations with large agencies?",
    "placement": "Will this feature prevent business from shifting to competitor carriers?",
}
