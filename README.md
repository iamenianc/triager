# von-triage

Severity triage scorer for the life-insurance quoting platform. A defect report
goes in; a 1–5 severity band comes out. Feature-request triage is not supported.

## Flow

One flow: software bugs and defect reports.

## Scoring

The scorer asks its 4 severity probes of the local decision model `von`
through the Ollaya server. von returns a probability in 0–1 per probe. Each probe
covers one axis of the severity rubric and is answerable from any writing style,
terse or verbose.

The 4 probabilities are summed as floats with no rounding, giving a continuous sum
in 0–4. The exact sum is compared against the band cuts.

Every probe is prefaced with the goal statement — "Your goal is to
accurately triage user bug reports." — which steadies von across writing styles.

Probes (each prefaced as above):

- `dmg` (destroys, corrupts, or miscalculates client data, records, or money, or exposes private client information), `block` (stops someone finishing their work or forces redoing it), `client_visible` (happens in front of clients or affects client documents), `all` (meaningfully impacts 100% of the user base)

Probe wording is load-bearing: von scores each option at its own `[MASK]` marker,
so the question text *is* the context it reasons over. Do not shorten the probes.

Band cuts (0–4 sum scale):

- ≤ 0.841 → 1, ≤ 1.577 → 2, ≤ 1.77 → 3, ≤ 3.372 → 4, else 5

The cuts are fitted under an **asymmetric error cost**: over-rating severity costs
double what under-rating costs (prefer to under-rate — a too-high band burns
escalation capacity on trivia; a too-low band still surfaces one band later).
Ties break toward exact hits, then within-1, then the higher band-5 cut.

Damage-dominance rules (applied after the cuts). The damage probe covers wrong
money, wrong data, lost records, and privacy exposure — the rubric's hard signal —
and must not be outvoted by the softer probes. Battery-verified precision: no case
in bands 1–4 reads `dmg` ≥ 0.88 (max 0.87, outdated rate tables), while the one-line
wrong-money canary reads a stable 0.89:

- `dmg` ≥ 0.88 → band at least 5; `dmg` ≥ 0.70 → band at least 4

Accuracy, cuts fitted on the battery's 32 cases (in-sample): 50% exact,
97% within one band (5 over / 11 under). One two-band miss remains: `d30` (want 1,
sum 1.55) and `d01` (want 5, sum 1.79) are 0.24 apart in sum but four bands apart
in label, so no cut placement removes every two-band error. A full battery run
takes about half a minute.

## What the bands mean

**Defect score** — how badly the defect hurts the business today.

- **1/5 — Trivial.** Purely cosmetic; nobody's work is affected (typo in help text, stale favicon).
- **2/5 — Minor annoyance.** Everything works, just untidy or slightly harder to use (misaligned button, saved cases not sorted newest-first).
- **3/5 — Real friction.** Slows advisors down or forces a workaround, but nothing is wrong, lost, or blocked (slow exports, intermittent freezes, cents-off rounding).
- **4/5 — Serious.** Advisors get stuck or lose meaningful work (validation blocking applications, drafts vanishing, wrong premium tables).
- **5/5 — Critical.** Money is wrong, data is lost, the system crashes, or documents are non-compliant — hitting many brokers across product lines with no workaround, often in front of clients.

Reading the score: the probes ask about substance and consequences, not tone, so an
understated report of a ledger-corrupting bug still scores 5/5. Adjacent scores mean
"roughly the same urgency" (within-one-band rate is 97%).

## Files

- `von-triage.py` — scorer and per-flow band cuts. Entry point.
- `von_branches.py` — the probe question sets. Key order and wording are load-bearing; von is option-order sensitive and the questions ask about consequences and magnitude.
- `battery.py` — the 32-case calibration battery: defect reports written in a standard, objective, unemotional, professional register by a business user.
- `battery_harness.py` — scores the battery, fits the band cuts under the asymmetric error cost, reports accuracy with a per-case breakdown.

## Requirements

- Python 3.8+ (standard library only — no pip packages)
- Ollaya server 0.9.0+ running with `von` loaded (`ollaya run von`), listening on
  `http://localhost:11435`
- The `von` model: ModernBERT-large, ONNX, 395M parameters (F32), 1.48 GiB
- ~2–3 GB free RAM while the model is resident; ordinary multi-core CPU, no GPU
  (the 4 probes take about 1 second on CPU)

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
python von-triage.py "The quoting engine shows wrong rider costs."
python von-triage.py defect "text"          (leading 'defect' keyword accepted)
echo "text" | python von-triage.py
python von-triage.py -m <model> "text"      # default model: von
```

Recalibrate the bands against the battery (32 server calls, about half a minute —
also refits and reports the optimal cuts under the asymmetric cost):

```
python battery_harness.py
```
