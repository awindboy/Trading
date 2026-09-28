# V13 research instructions — HA proof/lock generation

Last synchronized: `2026-09-28`
Status: `BASELINE 0 FROZEN / HA-9 CANDIDATE / ACTUAL-TICK CHILD ECONOMICS RECONSTRUCTED / EVENT PARITY PENDING`
Market authority: `GOLD# ONLY`
Base GitHub `main` checked: `6ea22fe914a8a7cc459cb5bd939b8435335b77d6`

## 0. Resume order

1. repository `AGENTS.md`;
2. this file;
3. `V13_DOCUMENT_AUTHORITY_MAP_20260926.md`;
4. `V13_OBJECTIVE_AND_EVALUATION_UPDATE_20260928.md`;
5. `HANDOFF_V13.md`;
6. `RESEARCH_STATE_V13.md`;
7. `V13_BASELINE0_HA_MAX10_CONTRACT_20260926.md`;
8. historical HA-0..HA-8/X1/X2 contracts/receipts only when their evidence is
   needed;
9. `V13_HA9_ADDON_PROOF_LOCK_ACTION_CONTRACT_20260928.md`;
10. `results/V13_HA9_ADDON_PROOF_LOCK_RECEIPT_20260928.md`;
11. `V13_HA9_MQL5_VALIDATION_PROTOCOL_20260928.md` before tester work;
12. `mt5/experts/V13HAProofLockMax10EA.mq5` before implementation changes.
13. `V13_HA9_TRADE_MODE_RESEARCH_BACKLOG_20260928.md` and
    `V13_HA9_TRADE_MODE_COVERAGE_20260928.md` before further mechanism work.

Later GitHub commits always outrank this package.

## 1. Baseline 0 remains frozen as comparator

Standard H4 HA formulas, Journey/color semantics, max-10 successful Child
entries and opposite-H4 close/reverse remain unchanged. Do not silently change
Baseline 0 when evaluating HA-9.

## 2. Current strategy candidate: HA-9

Only add-on Child management changes.

- Child #1 is unchanged.
- Child #2..#10 enter at Baseline-0 timing.
- The immediately preceding completed signal H4 supplies the proof target:
  raw HIGH for LONG, raw LOW for SHORT.
- Proof must occur during the next H4.
- Proofed Child: virtual lock becomes `max(entry, signal high)` LONG or
  `min(entry, signal low)` SHORT; lock cannot trigger in the same proof
  observation.
- Unproven Child: close at the first executable print after one H4.
- Early-closed add-ons remain counted as successful Child numbers and are not
  backfilled.
- Opposite H4 HA closes all remaining positions and reverses as Baseline 0.

No initial Hard SL, TP, HASTOC/EMA/ADX/volume filter, ML score, session/news gate
or external-market condition is part of HA-9.

## 3. Revised research objective

The current goal is to make the **ordinary trade stream** less loss-heavy and
more consistently upward. The primary measurements are:

1. losing Child count/share;
2. non-flat win rate;
3. consecutive-loss length;
4. chronological trade-stream DD;
5. 10/25/50/100-trade block positive share and median P/L;
6. year slices;
7. P/L after removing the largest profitable Journeys.

Total net and PF are still reported. Right-tail sacrifice is a measured cost,
not an automatic rejection gate.

This supersedes earlier active-language such as “preserve the large continuation
tail” as a strategy objective. Historical receipts remain factual records.

## 4. Current measured HA-9 evidence

Causal M1/H4 audit, consumed 2024-01-01..2026-08-28:

```text
Baseline:  1,430 wins / 2,427 losses / 1 flat
           win rate 37.08%, net +8,147.11, PF 1.19995

HA-9:      2,151 wins / 1,685 losses / 22 flat
           win rate 56.07%, net +3,946.06, PF 1.17634

losses reduced: 742 (-30.6%)
trade-sequence max DD: 3,756.99 -> 1,283.65
max consecutive losses: 25 -> 14
```

All three year slices are positive under the idealized HA-9 reconstruction.
Top-10 profitable-Journey removal leaves Baseline `-5,785.30` versus HA-9
`+74.26` points.

These are not actual-tick tester economics. The supplied MT5 report later
reconstructed 3,858 canonical Children at `+$3,067.50`, 2,118 strict wins,
1,734 strict losses and six flats. That report establishes preliminary Child
economics but does not establish event-reason parity without its Journal.

## 5. Causal boundaries

- Completed-bar inputs only for signal/proof target construction.
- First tick of a new H4 cannot retroactively prove an expired Child.
- Lock starts only after proof, never inside the same proof observation.
- No future H4/M1 may influence an earlier Child decision.
- No hindsight recovery after a Child is closed.

## 6. Next work

Do **not** add another indicator/model first. Next priority:

1. obtain the Strategy Tester Journal/event stream for the supplied report;
2. compare proof/timeout/lock events with the Python causal audit;
3. explain the idealized-versus-actual loss-count/win-rate/DD divergence;
4. do not reopen rejected timeout, re-arm, runner or generic exit-horizon
   variants under a new label;
5. only after event parity and genuinely new evidence, consider a new mechanism
   branch; sizing remains unauthorized.

New-data validation is not the immediate research step unless explicitly chosen
later; first establish that the consumed-data breakthrough survives exact
execution semantics.
