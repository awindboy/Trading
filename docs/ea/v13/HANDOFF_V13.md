# V13 handoff

Last synchronized: `2026-09-28`
Status: `HA-9 BREAKTHROUGH CANDIDATE / ACTUAL-TICK CHILD LEDGER RECONSTRUCTED / EVENT PARITY AND TRADE-MODE RESEARCH NEXT`
Base GitHub `main`: `6ea22fe914a8a7cc459cb5bd939b8435335b77d6`

## Resume point

V13 Baseline 0 remains the frozen comparator. HA-7 was rejected; HA-8A and X1/X2
were useful negative observations but did not solve the economic loss problem.
The research objective has since been clarified: prioritize reduction of ordinary
losing Children and improvement of the typical equity path; do not automatically
reject a candidate because it cuts large continuation winners.

Read `V13_OBJECTIVE_AND_EVALUATION_UPDATE_20260928.md` before interpreting old
right-tail language.

## Current breakthrough candidate — HA-9

Child #1 remains Baseline 0. For add-ons only:

```text
enter normally after same-color signal H4
  -> one-H4 proof window
  -> LONG must break signal-H4 raw HIGH
     SHORT must break signal-H4 raw LOW

if proof:
  lock = max(entry, signal high) LONG
       or min(entry, signal low) SHORT
  lock active only after proof observation

if no proof by next H4 boundary:
  close that add-on Child
```

Early closure does not end the Journey and does not backfill the Child number.

## Verified consumed-data result

```text
structural comparator:
  965 closed Journeys
  3,858 closed Children
  Baseline +8,147.11 points

HA-9:
  losses 2,427 -> 1,685 (-742 / -30.6%)
  wins   1,430 -> 2,151
  non-flat win rate 37.08% -> 56.07%
  trade-sequence DD 3,756.99 -> 1,283.65
  max consecutive losses 25 -> 14
  net +3,946.06 / PF 1.17634
```

Year net:

```text
2024 +37.15
2025 +1,867.48
2026 +2,041.43
```

Top profitable Journey removal:

```text
remove top 5:  Baseline -1,504.63 / HA-9 +1,426.97
remove top 10: Baseline -5,785.30 / HA-9    +74.26
```

This is the first V13 candidate that materially improves the ordinary Child
stream instead of merely predicting HA reversal better.

## What changed about right-tail interpretation

Old HA-7/HA-8 evidence that some warnings hit huge winners remains true. It no
longer controls the research objective. Current rule:

> report tail cost, but judge the candidate first on loss reduction, win rate,
> loss streaks, ordinary block quality, drawdown and trimmed robustness.

Do not delete or rewrite frozen historical contracts to pretend this objective
always existed.

## Immediate next work

1. Verify proof/timeout/lock event reasons from the supplied actual-tick report
   against `research/v13/ha9_addon_proof_lock_audit.py`; the exact Child ledger
   join is not yet event-reason parity.
2. Run the predeclared fixed-entry counterfactual matrix for opposite H1 HA,
   one-H1 timeout extension, opposite FAST-H4 HA, standard-H4 HA and structural
   protection.
3. Diagnose the 734 canonical no-proof 4–8h add-on losses using only state known
   by the action timestamp.
4. Diagnose the 1,460 canonical sub-4h winning add-ons without treating future
   maximum favorable excursion as executable profit.
5. Test information-based re-arm on repeat-loss clusters only after the exit
   modes are defined.
6. Keep Journey persistence/runner roles separate from permission to add a new
   late Child. Sizing remains last.

The governing program is
`V13_HA9_TRADE_MODE_RESEARCH_BACKLOG_20260928.md`; phase-1 evidence is in
`results/V13_HA9_TRADE_MODE_PHASE1_RECEIPT_20260928.md`.

Completed after that phase:

- global opposite-H1, FAST-H4 and standard-H4 exits were rejected because they
  materially increased losing Children and loss streak/DD burden;
- a one-H1 timeout extension and a state-selected version looked favorable on
  consumed data but failed the short post-cutoff quasi-holdout;
- do not optimize another timeout length or add a rescue exception.

Resume with runner identification, information-based re-arm and separation of
an existing runner from a new late tactical Child. Read
`results/V13_HA9_COUNTERFACTUAL_EXIT_MATRIX_RECEIPT_20260928.md` first.

Information-based re-arm has now also been tested and rejected. One-failure
gates removed more winners than losses. A narrower two-failure gate removed 34
winners versus 31 losses on consumed data and then skipped four winners versus
one loss post-cutoff. Resume with runner-versus-new-add separation, not another
re-arm/cooldown variant. See
`results/V13_HA9_INFORMATION_REARM_RECEIPT_20260928.md`.

Runner/tactical separation has also been tested. A first-proven FAST runner
restores a large right tail but adds 210 losses and worsens streak/DD. H1-close
acceptance narrows the damage but still adds losses and failed post-cutoff.
Suppressing new add-ons while a runner lives removes substantially more winners
than losses. Do not proceed to sizing or a C10 veto. See
`results/V13_HA9_RUNNER_TACTICAL_ROLE_RECEIPT_20260928.md`.

The trade-mode branch is now closed without an action promotion. Entry-method
selection and sizing were conditional downstream stages; neither is authorized
because no stable mode survived the post-cutoff checks. Use
`V13_HA9_TRADE_MODE_COVERAGE_20260928.md` to avoid repeating the 23 proposed
ideas under new labels.

## Do not resume with

- optimizing proof duration or an ATR offset on this consumed sample;
- adding HASTOC/EMA/ADX/volume/XGBoost to HA-9 before execution parity;
- treating total net reduction alone as failure;
- treating any touched large Journey as automatic failure;
- adding side/year exceptions from the current sample;
- changing Child #1 before the add-on mechanism is validated in actual ticks.
