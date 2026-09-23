# V11 post-stop chain selectivity diagnostic

Date: `2026-09-22`

Status: `CONSUMED DEVELOPMENT EVIDENCE / CORRECTION / NO TRADE, THRESHOLD, SIZING, OR PRODUCTION AUTHORITY`

## Why this diagnostic was necessary

The prior neutral-bridge report compared sparse admitted subsets with all `2,101` immediate FAST k1 candidates. Lower admitted stop rates did not mean that Wave information selectively removed losses. The strict +60m progress-and-efficiency slice rejected `1,405` candidates and retained only about half of baseline positive R. Its lower stop count was therefore not evidence that repeated-stop structure had been solved.

This diagnostic changes the unit of action. Immediate k1 remains active until an actual Hard-SL stop. Only then does a defensive state begin. Every tested intervention reports both the baseline stops prevented and the baseline non-stops and positive-R trades discarded.

## Baseline chain anatomy

The `636` k1 stops consist of:

- `468` first-position stops;
- `127` second consecutive stops;
- `34` third consecutive stops;
- `7` fourth consecutive stops.

Thus only `168/636` stops (`26.4%`) are repeats beyond the first stop. A mechanism that changes only post-stop authorization cannot remove the other `468` first stops. Eliminating only third-and-later stops would affect just `41` events.

## Stateful results

| Post-stop intervention | Stops | Prevented | Skipped non-stops | Skipped positive trades | Skipped positive R | Sum R | Repeat stops | 3rd+ stops | Max streak |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| baseline immediate k1 | 636 | 0 | 0 | 0 | 0.00 | 149.81 | 168 | 41 | 4 |
| +60m raw progress | 435 | 201 | 324 | 107 | 156.70 | 116.30 | 70 | 11 | 4 |
| +60m progress + efficiency | 374 | 262 | 479 | 184 | 323.28 | 60.15 | 60 | 6 | 3 |
| earliest tested efficient checkpoint | 456 | 180 | 235 | 73 | 106.55 | 99.05 | 63 | 5 | 3 |
| completed-NHA departure, one skip | 579 | 57 | 103 | 49 | 64.86 | 162.54 | 138 | 33 | 5 |
| completed-NHA departure, persistent | 562 | 74 | 140 | 63 | 81.36 | 171.62 | 136 | 36 | 5 |
| departure + Wave settlement, persistent | 554 | 82 | 151 | 66 | 85.77 | 177.34 | 132 | 34 | 5 |

`Completed-NHA departure` means that more than half of completed M5 closes settled beyond the previous actual H4 open in the prospective direction and the NHA close also finished beyond that open. This is a natural price relation, not an optimized numeric threshold.

## Decision

- The fixed bridge probes are **not** selective stop preventers. Their apparent stop reduction comes from rejecting hundreds of non-stop and positive-R candidates. Do not describe their admitted stop counts as losses cleanly avoided.
- Post-stop-only application improves the accounting but does not rescue the Wave-efficiency gate. It destroys too much positive R and total expectancy.
- Completed-NHA departure is a narrower lead because it preserved or increased consumed-data total R, but it prevented only `57-82` stops, reduced repeat stops only from `168` to `132-138`, and increased the maximum traded stop streak from four to five. It does not meet the objective.
- The current Wave Candle coordinates have not identified a structure that limits repeated stops to one or two while retaining good retries. V11 has a correct research target but not a successful transition mechanism.
- Do not request future validation for this mechanism yet. First-stop prevention and defensive-state release both require a materially better causal representation or action design on consumed development evidence.

## Reproduction

- Source episode ledger: `output/v11_neutral_bridge_final_20260922/V11_NEUTRAL_BRIDGE_EPISODES.csv`, SHA-256 `e4f87448c89472a2322692051e496a9b60c62adbe2401640c3660e3492b54e0d`.
- Script: `research/v11/analyze_v11_post_stop_chain.py`.
- Ignored output: `output/v11_post_stop_chain_20260922/`.
