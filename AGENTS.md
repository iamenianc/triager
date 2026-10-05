# Triager (von-triage) — session context

Severity triage scorer for a life-insurance quoting platform. A defect report
goes in; a 1–5 band comes out. Feature-request triage is deprecated; the focus
is purely bugs/defects. Repo: github.com/iamenianc/triager
(local: C:\Users\ianch\Hermes\Files\von-triage).

## Current production config

- Model: `von` (von 1.1, ModernBERT-large, ONNX, 395M params) served by Ollaya on
  `http://localhost:11435` — endpoint `/api/decide`, question types `noul` / `score` / `choice`.
  Other checkpoint available: `laya:en`, `laya:multilingual` (Laya, from Convai; 683–853 MB).
- Scorer: `von-triage.py` (CLI: `python von-triage.py defect|feature "<text>"`, `-m <model>` to override).
- Four probes, each prefaced with the goal statement
  (`"Your goal is to accurately triage user bug reports. "`):
  `dmg` (destroy/corrupt/miscalculate data, records, money, or expose private client information),
  `block` (stops work or forces redo), `client_visible` (happens in front of clients / affects client documents),
  `all` (meaningfully impacts 100% of the user base)
- Probes summed as floats, no rounding (0–4 scale), matched to cuts fitted
  under an ASYMMETRIC error cost (over-rating costs double under-rating; Ian's policy:
  prefer to under-rate). Ties break toward exact, within-1, then the higher band-5 cut:
  - ≤0.841 → 1, ≤1.577 → 2, ≤1.77 → 3, ≤3.372 → 4, else 5
- Damage-dominance rules, applied after the cuts (the rubric's hard signal must not be
  outvoted by softer probes; no battery case in bands 1–4 reads dmg ≥ 0.88, max 0.87):
  - `dmg` ≥ 0.88 → at least 5; `dmg` ≥ 0.70 → at least 4
- Battery: `battery.py` — 32 defect cases, written in a
  standard, objective, unemotional, professional business-user register.
  `battery_harness.py` scores it (~35 s), refits cuts under the asymmetric cost
  (it loads von-triage.py at runtime, so floors/cuts cannot drift), prints
  per-case results and probe discrimination. Last run: 50% exact / 97% within-1
  (5 over / 11 under) — in-sample, this is the
  only battery, so treat as calibration, not generalisation. The band-5 cut of 3.372
  puts several true-5 defects at 4 — accepted under the prefer-under-rate policy;
  wrong money still reaches 5 via the `dmg` ≥ 0.88 floor.

## Rules learned the hard way (do not relitigate without new data)

- **Probe wording is load-bearing on von.** von scores each option at its own `[MASK]`
  marker, so the question text *is* the context it reasons over. Shortening probes to
  4 words measurably destroyed discrimination (`manual` and `client_visible` went flat).
  Laya is the opposite: it compares state against option text, so short wording is fine.
- **`noul` answers carry no confidence** (always 0.0); `score` answers do. A confidence
  gate is therefore not available for probe-based scoring.
- **Weight multipliers don't generalise.** Fitting per-probe weights improved the fitting
  set but not the holdout — the cuts absorb a reweight. Dominance *rules* work; weights don't.
- **Register matters more than anything else tested.** The same scorer reads 50%/97% on
  the professional battery under the current asymmetric cuts (65%/87% under the old
  symmetric fit) and read ~42%/71% on a scrapped casual/teen-style set.
  von reads dramatic tone as severity (a footer typo in alarmist register scored 5/5) and
  understatement as low severity.
- Framings tested and rejected (all lost to the plain 4-probe scorer): single `score`
  question, single `choice` question picking the band directly, 24-probe set, 3-probe set,
  two-stage router with confidence gate, scripted 3-layer hierarchical tree (both `choice`
  and binary versions), shortened probes, weight multiplier search.
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
  Cuts are always refitted under the asymmetric cost; re-check the wrong-money canary
  (must score 5/5 — currently via the `dmg` ≥ 0.88 floor, not the sum).
- Verify server state directly (`/api/tags`, `/v1/models`) rather than assuming which
  models are loaded.

## Open items

- The battery is the only measurement set; a real-traffic holdout would give the first
  honest generalisation estimate.
- The defect side is sensitive to dramatic register — a model-level limit.
- `d30` (want 1, sum 1.55) and `d01` (want 5, sum 1.79) are inseparable by cuts — the
  surviving two-band defect miss trades against every other cut placement.
- Ollaya server binary: `C:\Users\ianch\AppData\Local\Programs\Ollaya\bin\ollaya.exe`
  (`pull` / `run` / `list` / `show`); models: `von:latest`, `laya:en`, `laya:multilingual`.
