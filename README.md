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
feature 18/29 exact, 28/29 within one band (bands scoring ±1 case between runs).

## Files

- `von-triage.py` — scorer and per-flow band cuts. Entry point.
- `von_branches.py` — the two 24-probe question sets. Key order and wording are load-bearing; von is option-order sensitive and the questions ask about consequences and magnitude.
- `von_battery.py` — 60-case calibration battery (31 defects, 29 features) with expected bands.
- `battery_collect.py` — runs the battery and writes per-probe probabilities to `battery_raw.json`.
- `battery_raw.json` — per-probe probabilities and expected bands for the 60 battery cases.
- `von_questions.json` — the question sets as JSON.

## Requirements

Ollaya server running with `von` loaded (`ollaya run von`), listening on
`http://localhost:11435`.

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
