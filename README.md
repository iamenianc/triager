# von-triage

Severity triage scorer for the life-insurance quoting platform. A defect report or a
feature request goes in; a 1–5 severity band comes out.

## Flows

Two discrete flows, chosen by the caller:

- `defect` — Tranche 1, software bugs and defects (24 probes)
- `feature` — Tranche 2, new feature requests (24 probes)

## Scoring

Each flow asks its branch's 4 severity probes of the local decision model `von`
through the Ollaya server. von returns a probability in 0–1 per probe. Each probe
covers one axis of the severity rubric and is answerable from any writing style,
terse or verbose.

The 4 probabilities are summed as floats with no rounding, giving a continuous sum
in 0–4. The exact sum is compared against the band cuts for that flow.

Every probe is prefaced with the flow's goal statement — "Your goal is to
accurately triage user bug reports." (defects) or "…feature requests." (features) —
which steadies von across writing styles.

Probes, per flow (each prefaced as above):

- defect — `dmg` (destroys, corrupts, or miscalculates client data, records, or money, or exposes private client information), `block` (stops someone finishing their work or forces redoing it), `client_visible` (happens in front of clients or affects client documents), `all` (meaningfully impacts 100% of the user base)
- feature — `rev` (not having it loses paying clients or business), `time` (saves a meaningful amount of daily time), `manual` (currently done by hand, in spreadsheets, or with outside tools), `all` (meaningfully impacts 100% of the user base)

Probe wording is load-bearing: von scores each option at its own `[MASK]` marker,
so the question text *is* the context it reasons over. Do not shorten the probes.

Band cuts, per flow (0–4 sum scale):

- defect: ≤ 1.09 → 1, ≤ 1.90 → 2, ≤ 2.35 → 3, ≤ 2.85 → 4, else 5
- feature: ≤ 0.90 → 1, ≤ 1.10 → 2, ≤ 1.69 → 3, ≤ 1.76 → 4, else 5

Damage-dominance rules (applied after the cuts). The damage probe covers wrong
money, wrong data, lost records, and privacy exposure — the rubric's hard signal —
and must not be outvoted by the softer probes. A high damage reading never occurs
on low-severity reports (0/18 cases in bands 1–3 across the batteries), so these
floors are precision-safe:

- defect: `dmg` ≥ 0.90 → band at least 5; `dmg` ≥ 0.70 → band at least 4
- feature: `rev` ≥ 0.60 **and** `all` ≥ 0.50 → band at least 5

Accuracy, cuts fitted on batteries A+B (120 cases): defect 53% exact, 93% within
one band; feature 50% exact, 68% within one band. On battery C (60 unseen
conversational cases) as a holdout: defect 39% exact, 81% within one band;
feature 45% exact, 79% within one band. A full battery run takes about 2.5
minutes per battery.

## What the bands mean

**Defect score (T1)** — how badly the defect hurts the business today.

- **1/5 — Trivial.** Purely cosmetic; nobody's work is affected (typo in help text, stale favicon).
- **2/5 — Minor annoyance.** Everything works, just untidy or slightly harder to use (misaligned button, saved cases not sorted newest-first).
- **3/5 — Real friction.** Slows advisors down or forces a workaround, but nothing is wrong, lost, or blocked (slow exports, intermittent freezes, cents-off rounding).
- **4/5 — Serious.** Advisors get stuck or lose meaningful work (validation blocking applications, drafts vanishing, wrong premium tables).
- **5/5 — Critical.** Money is wrong, data is lost, the system crashes, or documents are non-compliant — hitting many brokers across product lines with no workaround, often in front of clients.

**Feature score (T2)** — how much not having the feature costs the business.

- **1/5 — Novelty.** No workflow value (confetti animation, custom cursor colors).
- **2/5 — Nice-to-have.** A few users would enjoy it; no one loses anything without it.
- **3/5 — Convenience.** Saves real time for regular users; often requested, but nothing is lost or won without it.
- **4/5 — Competitive need.** Competitors have it or complaints are frequent; its absence is visible to the market.
- **5/5 — Revenue at risk.** Large agencies or carriers are withholding business, or producers are moving to competitors, because it is missing.

Reading the score: the probes ask about substance and consequences, not tone, so an
understated report of a ledger-corrupting bug still scores 5/5. Known leak: heavily
alarmist wording on a trivial bug can inflate the score by up to two bands (one
battery case). Adjacent scores mean "roughly the same urgency" (within-one-band
rate is 94% on defects, 100% on features).

## Files

- `von-triage.py` — scorer and per-flow band cuts. Entry point.
- `von_branches.py` — the probe question sets (3 in use per flow, full sets retained). Key order and wording are load-bearing; von is option-order sensitive and the questions ask about consequences and magnitude.
- `von_battery.py` — 60-case calibration battery (31 defects, 29 features) with expected bands.
- `battery_triple.py` — battery harness for the scorer: runs both batteries (120 cases), evaluates current cuts, refits cuts.

## Requirements

- Python 3.8+ (standard library only — no pip packages)
- Ollaya server 0.9.0+ running with `von` loaded (`ollaya run von`), listening on
  `http://localhost:11435`
- The `von` model: ModernBERT-large, ONNX, 395M parameters (F32), 1.48 GiB
- ~2–3 GB free RAM while the model is resident; ordinary multi-core CPU, no GPU
  (24 probes take about 3–4 seconds on CPU)

## Deployment on a new machine

Component footprint (the model is 95% of the total):

| Component | Download | Disk |
|---|---|---|
| von-triage repo | ~65 KB | <1 MB |
| Python 3.8+ | ~25 MB | ~100 MB |
| Ollaya server | ~10–50 MB | ~100 MB |
| `von` model | 1.48 GiB | 1.48 GiB |
| **Total** | **~1.6–1.7 GB** | **~1.8 GB** |

1. Install Python (or use any existing 3.8+).
2. Install Ollaya, then `ollaya pull von` and `ollaya run von` (leave it running —
   it listens on port 11435).
3. Clone or copy this repository.
4. `python von-triage.py defect "some bug text"`

Windows, macOS and Linux all work; nothing in the repo is OS-specific.

## Usage

```
python von-triage.py defect  "The quoting engine shows wrong rider costs."
python von-triage.py feature "Please add split-dollar funding solves."
echo "text" | python von-triage.py defect
python von-triage.py -m <model> defect "text"     # default model: von
```

Recalibrate the bands against the battery (60 server calls, about 30 seconds —
also refits and reports the optimal cuts):

```
python battery_triple.py
```
