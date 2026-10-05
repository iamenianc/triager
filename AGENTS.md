# Triager (von-triage) — session context

Severity triage scorer for a life-insurance quoting platform. A defect report or
feature request goes in; a 1–5 band comes out. Repo: github.com/iamenianc/triager
(local: C:\Users\ianch\Hermes\Files\von-triage).

## Current production config

- Model: `von` (von 1.1, ModernBERT-large, ONNX, 395M params) served by Ollaya on
  `http://localhost:11435` — endpoint `/api/decide`, question types `noul` / `score` / `choice`.
  Other checkpoint available: `laya:en`, `laya:multilingual` (Laya, from Convai; 683–853 MB).
- Scorer: `von-triage.py` (CLI: `python von-triage.py defect|feature "<text>"`, `-m <model>` to override).
- Four probes per flow, each prefaced with a goal statement
  (`"Your goal is to accurately triage user bug reports. "` / `"...feature requests. "`):
  - defect: `dmg` (destroy/corrupt/miscalculate data, records, money, or expose private client information),
    `block` (stops work or forces redo), `client_visible` (happens in front of clients / affects client documents),
    `all` (meaningfully impacts 100% of the user base)
  - feature: `rev` (not having it loses paying clients/business), `time` (saves meaningful daily time),
    `manual` (currently done by hand / spreadsheets / outside tools), `all` (same 100% question)
- Probes summed as floats, no rounding (0–4 scale), matched to per-flow cuts:
  - defect: ≤0.84 → 1, ≤1.22 → 2, ≤1.68 → 3, ≤2.17 → 4, else 5
  - feature: ≤0.80 → 1, ≤1.05 → 2, ≤1.08 → 3, ≤2.38 → 4, else 5
- Damage-dominance rules, applied after the cuts (the rubric's hard signal must not be
  outvoted by softer probes; a high damage reading never occurs in bands 1–3):
  - defect: `dmg` ≥ 0.90 → at least 5; `dmg` ≥ 0.70 → at least 4
  - feature: `rev` ≥ 0.50 and `all` ≥ 0.40 → at least 5
- Battery: `battery.py` — 60 cases (31 defect / 29 feature, 12 per band), written in a
  standard, objective, unemotional, professional business-user register.
  `battery_harness.py` scores it (~40 s), refits cuts + rules, prints per-case results
  and probe discrimination. Last run: defect 65% exact / 87% within-1; feature 55% / 90%
  (in-sample — this is the only battery, so treat as calibration, not generalisation).

## Rules learned the hard way (do not relitigate without new data)

- **Probe wording is load-bearing on von.** von scores each option at its own `[MASK]`
  marker, so the question text *is* the context it reasons over. Shortening probes to
  4 words measurably destroyed discrimination (`manual` and `client_visible` went flat).
  Laya is the opposite: it compares state against option text, so short wording is fine.
- **`noul` answers carry no confidence** (always 0.0); `score` answers do. A confidence
  gate is therefore not available for probe-based scoring.
- **Weight multipliers don't generalise.** Fitting per-probe weights improved the fitting
  set but not the holdout — the cuts absorb a reweight. Dominance *rules* work; weights don't.
- **Register matters more than anything else tested.** The same scorer reads ~65%/87% on
  the professional battery and read ~42%/71% on a scrapped casual/teen-style set.
  von reads dramatic tone as severity (a footer typo in alarmist register scored 5/5) and
  understatement as low severity.
- Framings tested and rejected (all lost to the plain 4-probe scorer): single `score`
  question, single `choice` question picking the band directly, 24-probe set, 3-probe set,
  two-stage router with confidence gate, scripted 3-layer hierarchical tree (both `choice`
  and binary versions), shortened probes, weight multiplier search.
  Best alternative found: `choice` framing on `laya:en` for features only.
- The batteries A/B/C (180 cases, verbatim-verbose / terse-intern / conversational-teen)
  were deliberately scrapped; their history remains in git before commit `575fefb`.

## Working style for this project

- Ian decides; report measurements, not opinions. When an experiment loses, say so plainly
  and leave production untouched.
- Keep rejected experiments out of the repo — measurement failures live in git history or
  on disk outside the repo, not in committed files.
- README is canonical current-state only: no history, no rejected approaches.
- After any probe/wording/cut change: run `battery_harness.py`, update `SUM_BANDS` in
  `von-triage.py`, the docstring accuracy line, and the README, then commit and push.
- Verify server state directly (`/api/tags`, `/v1/models`) rather than assuming which
  models are loaded.

## Open items

- The battery is the only measurement set; a real-traffic holdout would give the first
  honest generalisation estimate.
- Feature band-5 cases still undershoot when written casually (e.g. "or they'll walk"),
  and the defect side is sensitive to dramatic register — both are model-level limits.
- Ollaya server binary: `C:\Users\ianch\AppData\Local\Programs\Ollaya\bin\ollaya.exe`
  (`pull` / `run` / `list` / `show`); models: `von:latest`, `laya:en`, `laya:multilingual`.
