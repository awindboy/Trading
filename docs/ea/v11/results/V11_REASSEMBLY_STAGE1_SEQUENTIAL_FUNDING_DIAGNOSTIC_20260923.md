# V11 reassembly stage-1 sequential-funding diagnostic

Date: `2026-09-23`

Status: `CONSUMED DEVELOPMENT EVIDENCE / SELECTIVE BINARY FUNDING MODEL REJECTED / NO TRADE, WAIT, MODEL, SIZING, OR PRODUCTION AUTHORITY`

## Question

Can the complete causal V10 state choose between `fund now`, `continue observing`, and `do not fund` better than a fixed delayed-entry probe, without deleting the trade coverage and persistent-run right tail that make R7G valuable?

## Contract

- unit: one frozen R7G-intended FAST-k1 Child;
- test population: `626` non-warmup selected Children from 2024 through partial 2026;
- training population: prior-year FAST-k1 Children only;
- frozen feature views:
  - exact 84-coordinate V10 registry;
  - V10 registry plus causal completed-NHA/Wave/liquidity and checkpoint process state;
  - the same state plus R4 score, separate R5 `P(STOP)` and `E[R|non-stop]`, EV, and feedback coordinates;
- action checkpoints: immediate, +60m, +120m, +180m, or no funding;
- model: one fixed ridge decomposition of action availability, conditional stop probability, and conditional non-stop R;
- evaluation: complete-policy trade coverage, Hard SL, win rate, structural/weighted R, stop streak, drawdown, L6 positive-R retention, and equal-drawdown capacity.

The model was frozen at each calendar-year boundary. The 2024 test used 2022-2023 labels, the 2025 test used labels available before the first 2025 selected Child, and the 2026 test used labels available before the first 2026 selected Child. The existing R4/R5 heads have no pre-2024 event export, so the all-head view is reported only for 2025-2026.

## Compliance correction

The first implementation accidentally included future-only event-ledger columns such as `next_run_length`, current-run `nha_explanation`, and post-run progress labels in the process view. That output was rejected before documentation. The retained run explicitly excludes:

```text
immediate_nha
next_run_length
one/short-run triplet labels
pair/journey net progress at the later NHA
route_still_open_after_nha
current-run nha_explanation
L, run_end_decision, R, stop_hit
```

The retained process state uses only coordinates available at the decision or checkpoint, including the prior run-ending NHA explanation, completed decision-H4 Wave coordinates, causal liquidity context, and revealed checkpoint prefixes.

## Final result

The binary selector did not establish a superior funding policy. On the common 2025-2026 period:

| Policy | Trades | Hard SL | Win rate | Weighted R | 1% max DD | L6 positive-R retention | Equal-DD ending equity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| immediate R7G | 531 | 112 | 36.91% | +257.10R | 26.74% | 100.0% | 8.79x |
| fixed +180m survivor probe | 463 | 54 | 40.17% | +209.98R | 21.84% | 74.23% | 9.11x |
| all-parts sequential, stop cost 0.00 | 333 | 59 | 37.84% | +232.81R | 24.50% | 72.54% | 8.19x |
| all-parts sequential, stop cost 0.25 | 312 | 52 | 38.46% | +224.33R | 29.53% | 67.70% | 5.46x |
| all-parts sequential, stop cost 0.50 | 288 | 47 | 38.89% | +174.76R | 22.63% | 57.75% | 5.56x |

The all-parts view retained more weighted R than the fixed wait at its least defensive setting, but only by funding `62.7%` of candidates and retaining `72.5%` of L6 positive R. More defensive settings removed additional stops by deleting still more trades and right tail.

Across state/action/year cells, median out-of-year correlation between predicted action EV and realized action R was only about `0.03` for both the V10-only and all-parts views. The existing parts therefore do not yet forecast the relative value of the four funding times with useful stability.

## Decision

- Reject the Stage-1 ridge selector as funding authority.
- Do not promote any stop-cost value or feature view.
- Preserve the negative finding that adding Wave/process state did not solve binary selective admission.
- Retain the architectural distinction between candidate existence and capital deployment.
- Move the next test from `fund all or fund nothing` to `participate small, release the remaining ceiling separately`.

## Reproduction

- script: `research/v11/analyze_v11_reassembly_stage1.py`;
- ignored output: `output/v11_reassembly_stage1_20260923/`;
- corrected policy-ledger SHA-256: `c02b750c27e5f6c32ed9fe8b974f574861c2e80988f1a86fb664144173d48821`;
- raw event SHA-256: `c4348a34aa35d1e9793283cebbf1a028327c10e3e1c5a4fde2a9e74e3ff801a7`;
- causal episode SHA-256: `e4f87448c89472a2322692051e496a9b60c62adbe2401640c3660e3492b54e0d`.
