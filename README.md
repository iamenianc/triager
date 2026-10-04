# von-triage

Severity triage scorer for the life-insurance quoting platform. A defect report or a
feature request goes in; a 1–5 severity band comes out.

## Flows

Two discrete flows, chosen by the caller:

- `defect` — Tranche 1, software bugs and defects (24 probes)
- `feature` — Tranche 2, new feature requests (24 probes)

## Scoring

Each flow asks its branch's 24 yes/no probes (8 groups × 3) of the local decision
model `von` through the Ollaya server. von returns a probability in 0–1 per probe.

The 24 probabilities are summed as floats with no rounding, giving a continuous sum
in 0–24. Two reversed-polarity probes in the Workaround group (`meeting_wa`,
`self_resolve`) contribute `1 − p`; every other probe contributes `p`. The exact sum
is compared against the band cuts for that flow.

Band cuts, per flow:

- defect: ≤ 5.0 → 1, ≤ 6.4 → 2, ≤ 8.8 → 3, ≤ 11.0 → 4, else 5
- feature: ≤ 2.5 → 1, ≤ 4.3 → 2, ≤ 6.9 → 3, ≤ 12.0 → 4, else 5

Accuracy on the 60-case battery: defect 22/31 exact, 29/31 within one band;
feature 14/29 exact, 28/29 within one band (band cuts are chosen to maximise
close-miss tolerance, since a one-band error is acceptable in triage).

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

Reading the score: the scorer reads the substance of the text, not its tone — an
alarmist report of a trivial bug still scores 1/5, and an understated report of a
ledger-corrupting bug still scores 5/5. Adjacent scores mean "roughly the same
urgency" (within-one-band rate is 94% on defects, 97% on features).

## Files

- `von-triage.py` — scorer and per-flow band cuts. Entry point.
- `von_branches.py` — the two 24-probe question sets. Key order and wording are load-bearing; von is option-order sensitive and the questions ask about consequences and magnitude.
- `von_battery.py` — 60-case calibration battery (31 defects, 29 features) with expected bands.
- `battery_collect.py` — runs the battery and writes per-probe probabilities to `battery_raw.json`.
- `battery_raw.json` — per-probe probabilities and expected bands for the 60 battery cases.
- `von_questions.json` — the question sets as JSON.

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

Recalibrate the bands against the battery (60 server calls, about 4 minutes):

```
python battery_collect.py
```
