# V13 HA-7 first action Child-admission receipt

Date: `2026-09-27`
Status: `FIRST ACTION EXPERIMENT COMPLETE / REJECTED / NO EA CHANGE`
Contract: `V13_HA7_FIRST_ACTION_CHILD_ADMISSION_CONTRACT_20260927.md`
Base GitHub main HEAD: `40f97352e47c66cd3b952f74532b1b71969e79fd`

## 1. Frozen action tested

On an existing Journey continuation bar with original `journey_bar` 2..10:

```text
h1_path_state == persistent_opposition
AND relative_tick_volume20 > 1.0
```

suppress only that bar's scheduled add-on Child. Existing Children and the Journey stay open. Child #1 is never vetoed. No skipped Child is backfilled; original bar slots 1..10 remain the admission horizon. No other strategy rule changes.

`1.0` means above the causal same-H4-slot trailing-20 median and was frozen before economic measurement; no threshold sweep was run.

## 2. Baseline parity

Idealized next-H4-open structural reconstruction reproduced the frozen sanity ledger:

```text
closed Journeys: 965
closed Children: 3,858
net points: +8,147.11
Child PF: 1.19995
Journey PF: 1.25972
realized-Journey max DD diagnostic: 3,659.45 points
```

## 3. Variant result

```text
admitted Children: 3,769
skipped Children: 89
variant net points: +8,069.18
change vs Baseline: -77.93 points
Child PF: 1.20182
Journey PF: 1.26232
realized-Journey max DD: 3,690.36
DD change: +30.91 points (worse)
```

PF moved slightly upward only because the removed set contained both large winners and losers; net points and realized drawdown both worsened. The action therefore fails the primary structural economic test.

## 4. What the veto removed

The 89 skipped baseline Children had:

```text
net contribution: +77.93 points
gross profit: +841.61
gross loss: -763.68
wins/losses: 38 / 51
median Child P/L: -1.58 points
```

Although more skipped Children lost than won, the retained winners were economically larger. Win count alone therefore gave the wrong action conclusion.

## 5. Instability by year and side

Variant net change from removing the frozen trigger:

```text
2024 SHORT  +83.73
2024 LONG   -37.69
2025 SHORT +115.86
2025 LONG   +96.46
2026 SHORT -305.01
2026 LONG   -31.28
```

The action is not stable across years/sides. The 2026 SHORT damage alone exceeds the positive contribution in several earlier slices.

## 6. Right-tail damage

For Journeys lasting at least 10 H4 bars:

```text
baseline first-10-slot Children: 880
baseline net from those Children: +31,131.36
vetoed long-Journey Children: 15 across 15 Journeys
original net contribution of vetoed Children: +341.09
wins/losses among vetoed long-Journey Children: 11 / 4
variant long-Journey net: +30,790.27
```

Thus the proposed veto specifically removes profitable exposure from the long Journey tail V13 is required to preserve.

## 7. Concentration

The trigger appeared in 87 Journeys. Removing it helped 49 Journey aggregates and hurt 38, but the positive/negative magnitudes were highly uneven. The largest harmful removed winners were approximately `122.84`, `121.62`, `119.11`, and `110.27` points. The result is therefore not a clean broad-based improvement hidden by a few outliers.

## 8. Decision

`REJECT HA-7 CHILD-ADMISSION VETO`.

Do not:

- change the EA;
- tune the `1.0` threshold;
- search Child-slot cutoffs;
- add side/year exceptions;
- convert the same state into an exit;
- use the observed late-slot losses to invent a fixed late-Child rule.

The experiment demonstrates why descriptive transition probability is not enough: a state can have elevated reversal hazard while the minority continuation outcomes still carry economically dominant right-tail value.

## 9. Research implication

HA-0..HA-6 have now exposed several causal transition states, but deterministic single-rule exits/vetoes repeatedly damage persistent Journey tails. The next justified roadmap step is not more threshold mining. It is HA-8's state-model baseline: estimate lifecycle probability/remaining-excursion conditionally from the already-measured causal representation, using chronological out-of-fold prediction and simple interpretable models before any action mapping.

This HA-7 result is consumed development evidence only and does not alter Baseline 0.
