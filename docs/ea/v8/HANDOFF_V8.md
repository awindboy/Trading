# V8 Development Handoff

Last updated: `2026-09-03`
Current phase: `V8-A-N-SLOW / REALISTIC CHRONOLOGICAL ACCOUNT REPLAY IS THE IMMEDIATE NEXT ACTION`
Production authority: `NONE`
Market: `GOLD#`
Open development evidence: `2022-2026`
Untouched reserve: `GOLD# 2021`
Base Git HEAD expected before apply: `0b7dab2b0b61be3deadd2908060e6e8ebb718b28`

## 1. Immediate instruction to the next session

**Do not start another strategy variant, indicator family, threshold search, market-context branch, or P0/P2 comparison before completing the already-defined chronological account replay.**

The user explicitly wants the practical question answered now:

> If one executable V8 policy had actually traded through the open development period, what would the account path have looked like?

This is an account/execution replay question, not another P0-vs-P2 research comparison.

Use the supplied `V8_PHASE0_REALISTIC_REPLAY_PROBE_20260903.zip` or reproduce exactly the same frozen policy. If replay results are supplied, analyze them directly before opening any new research branch.

## 2. Frozen architecture semantics

```text
ONSET
0.25 H4 ATR / P15 fresh75
= excursion / movement-episode onset

-> directional M1-close reveal
-> pullback
-> reclaim = ACCEPTANCE

ACCEPTANCE QUALITY
micro3 = prog1 + run_accept + prog3

DYNAMIC STRUCTURAL STATE
PRISTINE / DAMAGED / CLOSE_BROKEN
+
geometry/process survival hazard

WINNER CONTINUATION
realized early progress, especially MFE15/S,
within a surviving structure
```

P15 is not terminal direction/persistence.
Retention is not movement.
Winner continuation is a separate downstream question.

## 3. Exact Slow-N downstream authority

Per project direction, do not reopen historical reconstruction differences without a direct contradiction.

```text
P0
2024 fresh75 648 -> acceptance 281
2025 fresh75 533 -> acceptance 234
2026 fresh75 322 -> acceptance 154

P2
2024 fresh75 735 -> acceptance 318
2025 fresh75 583 -> acceptance 239
2026 fresh75 291 -> acceptance 144
```

P0 and P2 are alternate deterministic training-sample realizations. They are robustness realizations, not two strategies to merge opportunistically.

## 4. Structural-retention authority

Primary acceptance family:
`fresh75 -> <=15m 0.25ATR M1-close reveal -> >=25% pullback with origin retained -> M1-close reclaim`.

Exact-population micro3 AUC:

```text
15m P0 .720/.756 ; P2 .742/.755
30m P0 .701/.723 ; P2 .699/.710
60m P0 .705/.722 ; P2 .702/.705
```
(2025/2026)

micro3 remains an acceptance-time structural-quality prior. After strong causal geometry/process controls, repeatedly recomputed micro3 adds approximately zero robust incremental AUC and must not become a dynamic voter.

## 5. Structural-state correction

Use:

```text
PRISTINE     = pullback-extreme wick intact
DAMAGED      = wick breached but M1-close integrity retained
CLOSE_BROKEN = M1 close breaches the structural extreme
```

Wick damage is not terminal reversal. Close damage is more serious but is still not automatically the executable trade stop.

Post-break equal-distance direction is approximately chance; do not use break as reversal alpha.

## 6. Practical movement / payoff authority

The critical correction is:

```text
structure survived != price moved far in the accepted direction
```

Broad causal discovery showed that longer survival by itself mostly predicts additional survival, not a materially larger next-15m excursion.

Among full-horizon retained events, median MFE grows with horizon but many structures survive while barely paying:

```text
15m retained median MFE ~0.21S
30m retained median MFE ~0.33S
60m retained median MFE ~0.50S
```

At t15 among structurally alive events, actual realized progress separates later runner potential strongly. Using first-15m MFE/S:

```text
MFE15 <0.10S  -> future45 >=0.50S only ~5-6%, survive45 ~38-44%
MFE15 >=0.50S -> future45 >=0.50S ~30-35%, survive45 ~73-82%
```

The monotonic relation persists across 2022-2026 and both directions in broad discovery.

Geometry-control stress:
- for modest future +0.25S movement, progress adds little over geometry;
- for larger future +0.50S movement, progress adds meaningful incremental discrimination after nonlinear geometry in later-year tests;
- +0.75S incremental evidence is positive but less stable in 2026 and must not be overstated.

Exact Slow-N close-intact runner continuation evidence remains:
`MFE15/S` AUC roughly `.657-.716` for future +0.50S and `.745-.820` for future +0.75S across P0/P2 2025/26.

This is a **winner-continuation signal**, not an initial entry permission signal.

## 7. Directional economic viability result

A wide set of causal GOLD-internal formulations failed to robustly rank the economic direction of an already-formed ACCEPTANCE:
- auction/local-liquidity context;
- persistence/mean-reversion state;
- reveal purity/commitment;
- six-hour session state;
- transfer of old N2 M1 synchronization;
- transfer of B34 recent-15m signed efficiency.

Their later-year AUCs were generally near chance.

Therefore close the branch:
`static GOLD-internal ACCEPTANCE direction filter mining`.

Do **not** generalize this negative result to movement onset, structural retention, damage-state estimation, or winner continuation. Those answer different questions and remain preserved evidence.

## 8. Capital-allocation correction

For the user's `$1,000` account, `0.01 lot` minimum, and `1:1000` leverage, the old conceptual 50/50 split is not executable at the smallest base size.

Executable research decomposition:

### Routine base
- ACCEPTANCE -> 0.01 lot.
- next executable M1 open.
- TP `+0.25S`.
- SL `-0.25S`.
- max lifecycle `240m`.

### High-Q runner re-entry
- only after ACCEPTANCE+15m.
- structure M1-close intact through 15m.
- use the previously frozen 2024 P0 high-progress reference `MFE15 >= 0.555S` for the current replay; do not re-fit it from later P/L.
- enter at next executable M1 open.
- TP `+0.75S`.
- SL `-0.40S`.
- max lifecycle `60m` for the current replay probe.
- size in 0.01-lot increments so stop risk is at most `2%` of current floating equity; floor the lot size.
- if 0.01 lot already exceeds the risk budget, skip the runner.

The capital idea is causal:
`frequent small opportunity -> market demonstrates runner-grade progress -> allocate more later`.

Do not increase size merely because predicted retention or P15 is high.

## 9. Chronological replay contract

The current account replay is one single execution path:

- population/signals: **P0 Phase-0 only**;
- trade chronologically through 2024 -> 2025 -> 2026;
- do not mix P2 trades into the account;
- starting balance `$1,000`;
- minimum/step `0.01 lot`;
- leverage `1:1000`;
- allow overlapping positions and measure concurrent exposure;
- raw M1 OHLC treated as Bid; Ask = Bid + `SPREAD * 0.01` for this GOLD# feed;
- LONG enters Ask/exits Bid; SHORT enters Bid/exits Ask;
- if TP and SL are both reachable in one M1 bar, use **SL-first**;
- enforce margin checks;
- report realized balance and floating equity, not only aggregate R;
- report annual/monthly results, DD, max loss streak, max concurrency, initial-risk concentration, skipped runner signals, and cost sensitivity.

Raw GOLD M1 authority used in this session:
- expected SHA256 `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`.

Exact P0 acceptance counts must fail-closed at:
`2024 281 / 2025 234 / 2026 154`.

## 10. Research-inference guardrail

Read `DECISIONS_V8_RESEARCH_INFERENCE_GUARDRAILS_ADDENDUM_20260903.md` before any new negative verdict.

Permanent rule:

```text
component failure != transfer failure != exit failure != capital-allocation failure != full strategy failure
```

A negative wrapper does not erase a supported upstream mechanism unless it directly contradicts that mechanism.

Do not create a new variant merely because a viewed P/L table is disappointing.

## 11. What comes after the replay

Only after the chronological replay is analyzed:

1. decide whether the current executable wrapper is economically viable as-is;
2. identify whether any weakness is direction, entry, exit, exposure, or minimum-lot/capital granularity;
3. preserve supported upstream modules even if the wrapper is negative;
4. only then open the already-preregistered source-of-move / market-universe transfer work if it is still the correct next question;
5. keep the outcome-blind external universe frozen as `USDJPY# / XAUEUR# / BTCUSD#` if that branch proceeds;
6. do not use 2021.

## 12. Reading order

1. `AGENTS_V8.md`
2. this file
3. `DECISIONS_V8_RESEARCH_INFERENCE_GUARDRAILS_ADDENDUM_20260903.md`
4. `V8_SEQUENTIAL_CAPITAL_ALLOCATION_RESEARCH_20260903.md`
5. `V8_DIRECTIONAL_ECONOMIC_VIABILITY_FALSIFICATION_20260903.md`
6. `V8_A_N_SLOW_PRACTICAL_MOVEMENT_CHARACTERIZATION_20260903.md`
7. `V8_A_N_SLOW_DYNAMIC_STRUCTURAL_STATE_RESEARCH_20260903.md`
8. `V8_A_N_SLOW_PERSISTENCE_RETENTION_RESEARCH_20260902.md`
9. `DECISIONS_V8_PERSISTENCE_RETENTION_ADDENDUM_20260902.md`
10. `V8_SLOWN_SOURCE_OF_MOVE_AND_MARKET_UNIVERSE_CONTRACT_20260903.md` only after account replay context is understood
11. older V8 state/backlog docs as needed

Always refresh GitHub HEAD first. If the repository has moved beyond the expected base, inspect the new commits before applying or replacing files.
