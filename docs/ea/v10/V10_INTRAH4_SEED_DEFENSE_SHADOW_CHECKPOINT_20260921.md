# V10 Intrabar Seed-Defense Shadow Checkpoint

Date: `2026-09-21`
Status: `POST-HOC DEVELOPMENT FINDING / FUTURE-ONLY SHADOW / NO TRADE AUTHORITY`
Market: `GOLD# ONLY`
Base GitHub `main`: `438f6b4d588330b4cd2f1cae7cba968f14df36e4`

## 1. Research decision

The forming-H4 HA forecast is not promoted as a general exit engine.  The
tested action-value regression and broad NHA-warning exits destroy too much
right-tail value.

A narrower hypothesis survives as future-only shadow instrumentation:

```text
existing R7G-selected newest Child
+ r7g_weight == 1
+ still alive at forming-H4 +60m
+ direction-aligned provisional FAST-HA margin / prior H4 ATR180 <= frozen q10
-> hypothetically exit that newest 1-unit Child only
```

The rule does not change the original entry, Hard SL, a 3-unit Child, older
campaign Children, catch-up behavior, or any EA order.

## 2. Why the broad action-value path was rejected

A fixed Ridge action-value model was trained to predict:

```text
r7g_weight * (exit_at_+60m_R - hold_R)
```

It used the causal +60-minute HA probability/state, current Child economics,
and frozen R7G fields.  Outer-year results were poor:

| Test year | Rows | R2 | Policy delta R |
|---:|---:|---:|---:|
| 2025 | 730 | 0.0132 | -35.46R |
| 2026 | 465 | -0.0529 | -21.64R |
| Pooled | 1,195 | — | -57.10R |

Run-block bootstrap for pooled delta R was `[-168.43R, +43.66R]` at 95%, with
`P(delta > 0) = 0.145`.  A simpler `NHA q90 + currently losing` rule also lost
`-8.89R`.

Therefore neither a more complex value model nor the intuitive current-loss
condition is supported by the consumed evidence.

## 3. Deterministic seed-defense diagnostic

The surviving coordinate deliberately removes the M1/M5 classifier.  The
earlier checkpoint found that those features did not improve discrimination
over the normalized provisional HA margin itself.

For each test year, q10 was computed only from +60-minute opportunity prefixes
available before that year:

| Test year | Prior q10 | Actions | Final NHA | Good / bad actions | Hard SLs prevented | Delta R |
|---:|---:|---:|---:|---:|---:|---:|
| 2024 | -0.147883 | 3 | 3 | 3 / 0 | 2 | +1.3533R |
| 2025 | -0.154273 | 11 | 10 | 9 / 2 | 3 | +1.8523R |
| 2026 | -0.164694 | 10 | 10 | 7 / 3 | 3 | +1.4845R |
| Pooled | — | 24 | 23 | 19 / 5 | 8 | +4.6900R |

Additional diagnostics:

```text
baseline Hard SL count        184
shadow Hard SL count          176
maximum Hard-SL streak        4 -> 4
L6+ positive-R retention      100.0078%
run-block bootstrap 95%       [+1.05R, +8.64R]
bootstrap P(delta > 0)        0.99445
```

This is economically different from a full NHA exit.  The warning is applied
only to the low-conviction 1-unit seed, while the R7G 3-unit opportunity lane
is left untouched.  That sharply limits false-positive tail damage.

## 4. Evidence limits

This is not independent validation:

1. `q10` and the 1-unit seed restriction were identified after inspecting
   consumed 2022-2026 development results.
2. Only 24 historical actions fired across 2024-2026.
3. The bootstrap describes uncertainty conditional on this selected rule; it
   does not remove post-selection bias.
4. The rule reduced total Hard SLs but did not shorten the maximum historical
   consecutive-stop streak.

The finding is therefore a precise candidate for observation, not evidence
for strategy or EA promotion.

## 5. Frozen future shadow contract

For observations strictly after the frozen source cutoff:

```text
hypothesis                 V10_INTRAH4_SEED1_Q10_DEFENSE
checkpoint                 exact forming-H4 +60 minutes
eligible Child             R7G-selected newest Child, weight 1, still alive
coordinate                 direction * (provisional FAST-HA close
                           - fixed FAST-HA open) / prior completed H4 ATR180
frozen threshold           <= -0.1641973584634039
shadow action              hypothetical exit newest 1-unit Child only
3-unit Child action        none
older Child action         none
catch-up                   none
threshold/model scan       none
trade/EA authority         none
```

The first forward audit must report event count, final PHA/NHA, good and bad
actions, Hard SLs prevented, delta R, tail regret, stop streaks, direction and
time concentration.  A small positive sample must not be promoted.

## 6. Reproducibility

Code:

```text
research/v10/analyze_v10_intrah4_action_value.py
research/v10/freeze_v10_intrah4_seed_defense_shadow.py
```

Generated local evidence (removed during the 2026-09-21 repository cleanup; rerun the retained scripts to regenerate):

```text
output/v10_intrah4_action_value_20260921/
output/v10_intrah4_seed_defense_20260921/V10_INTRAH4_SEED_DEFENSE_OUTER_SCORED.csv
output/v10_intrah4_seed_defense_20260921/V10_INTRAH4_SEED_DEFENSE_OUTER_SUMMARY.csv
output/v10_intrah4_seed_defense_20260921/V10_INTRAH4_SEED_DEFENSE_BOOTSTRAP.csv
output/v10_intrah4_seed_defense_20260921/V10_INTRAH4_SEED_DEFENSE_FUTURE_SHADOW_MANIFEST.json
```

Frozen source hashes and the exact threshold are recorded in this checkpoint.
All historical rows used here remain consumed development evidence.
