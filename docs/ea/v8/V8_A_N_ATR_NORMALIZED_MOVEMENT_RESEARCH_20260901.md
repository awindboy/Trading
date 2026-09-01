# V8-A-N ATR-Normalized Movement Research — 2026-09-01

Status: `RETAINED RESEARCH CHALLENGER / NO PRODUCTION AUTHORITY`
Market: `GOLD#`
Base Git HEAD: `a49a351ff988c3d16698080773ee7a4d3474ffda`
Untouched reserve: `GOLD# 2021`

## 1. Research question

Frozen V8-A/V8-A2 ask an absolute-dollar question:

```text
P(reach C0 +/-$10 within 15m / 30m / 60m)
```

The fixed $10 barrier changed effective difficulty dramatically as GOLD price level and volatility changed.

This study asks whether a causal volatility-normalized target is structurally more portable:

```text
scale(t) = M5 Wilder ATR14 available before the decision
barrier = k * scale(t)
k in {0.75,1.00,1.25,1.50,1.75,2.00,2.50,3.00}
```

V8-A and V8-A2 remain unchanged controls.

The new branch is named:

`V8-A-N = ATR-NORMALIZED MOVEMENT CHALLENGER`.

## 2. Pipeline parity before new claims

The 86-feature A2 pipeline was reconstructed first.

Using the existing official A2 coefficient pack reproduced the documented outer-year AUC, including:

```text
2024 P15 = 0.8660052
2025 P15 = 0.8736183
2026 P15 = 0.8190162
```

The factual event census also reproduced the established population.

Therefore the normalized comparison uses the same causal feature/event/evaluation framework rather than a new unrelated pipeline.

## 3. Fixed $10 is not a stable target difficulty

All completed M5 states show the following fixed-$10 movement base rates:

| Horizon | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---:|---:|---:|---:|---:|
| 15m | 0.57% | 0.38% | 1.04% | 7.34% | 28.83% |
| 30m | 1.65% | 1.19% | 3.10% | 16.34% | 48.75% |
| 60m | 4.42% | 3.64% | 8.12% | 31.05% | 71.27% |

The same nominal barrier represented a radically different volatility-relative excursion across years.

## 4. ATR normalization nearly removes the base-rate drift

For `barrier = 2.0 * pre-decision ATR14`:

| Horizon | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---:|---:|---:|---:|---:|
| 15m | 18.41% | 18.77% | 18.61% | 18.50% | 18.19% |
| 30m | 40.57% | 40.00% | 40.04% | 40.13% | 39.20% |
| 60m | 66.81% | 64.91% | 65.13% | 66.38% | 65.63% |

This is the strongest structural result of the study.

The claim is not that 2ATR is automatically the correct trading barrier. The claim is that volatility-normalized excursion has substantially more stable meaning across calendar regimes than fixed $10.

## 5. Normalized excursion distribution is also stable

Maximum absolute future excursion divided by pre-decision ATR14 has very stable medians:

| Horizon | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---:|---:|---:|---:|---:|
| 15m | 1.229 | 1.223 | 1.227 | 1.222 | 1.207 |
| 30m | 1.765 | 1.738 | 1.740 | 1.746 | 1.723 |
| 60m | 2.522 | 2.490 | 2.480 | 2.514 | 2.479 |

The corresponding dollar excursion distribution changed dramatically.

This supports treating:

```text
future excursion / causal volatility scale
```

as a more portable movement target.

## 6. Prototype V8-A-N surface

Separate A2-style four-class survival models were trained for:

```text
0.75 ATR
1.00 ATR
1.25 ATR
1.50 ATR
1.75 ATR
2.00 ATR
2.50 ATR
3.00 ATR
```

Each produces P15/P30/P60 for reaching that normalized distance.

Example: `1.25 ATR` factual-event outer AUC:

| Horizon | 2024 | 2025 | 2026 |
|---|---:|---:|---:|
| P15 | 0.720 | 0.687 | 0.675 |
| P30 | 0.738 | 0.700 | 0.703 |
| P60 | 0.800 | 0.752 | 0.750 |

Normalized-target AUC is lower than fixed-$10 A2.

This is not automatically negative: fixed-$10 A2 can exploit the fact that high volatility makes a fixed $10 easier. V8-A-N deliberately removes much of that trivial barrier-difficulty information and asks the harder question:

`will price travel unusually far relative to current volatility?`

V8-A-N therefore complements, rather than replaces, absolute-dollar A2 at this stage.

## 7. Distance-surface monotonicity issue

The prototype trains each ATR distance independently.

This can rarely produce an impossible relationship such as:

```text
P(reach 2.0 ATR) > P(reach 1.75 ATR)
```

Observed any-distance violation rate was small but non-zero:

```text
P15 roughly 0.04% to 0.12% by year
P60 up to roughly 0.89%
```

A final V8-A-N implementation must enforce:

```text
longer horizon => probability non-decreasing
farther distance => probability non-increasing
```

Prefer a joint ordinal/survival surface or an explicitly monotonic reconstruction.

Do not deploy the independent-distance prototype as a final live probability surface.

## 8. Normalized fresh-high trigger

A fresh high-probability trigger is defined separately for each normalized barrier:

```text
previous completed M5 P15(k ATR) < 75%
current completed M5 P15(k ATR) >= 75%
```

This is a movement trigger only. It does not determine LONG/SHORT.

### 1.25 ATR trigger

| Year | N | 15m actual hit | 30m | 60m |
|---|---:|---:|---:|---:|
| 2024 | 1958 | 81.38% | 95.18% | 99.49% |
| 2025 | 2230 | 79.03% | 94.43% | 99.28% |
| 2026 | 1690 | 77.09% | 93.78% | 98.86% |

### 1.50 ATR trigger

| Year | N | 15m actual hit | 30m | 60m |
|---|---:|---:|---:|---:|
| 2024 | 809 | 81.64% | 93.92% | 98.88% |
| 2025 | 834 | 77.85% | 91.77% | 98.18% |
| 2026 | 551 | 80.04% | 93.77% | 97.80% |

### 2.00 ATR trigger

| Year | N | 15m actual hit | 30m | 60m |
|---|---:|---:|---:|---:|
| 2024 | 180 | 80.90% | 91.01% | 97.75% |
| 2025 | 151 | 73.29% | 88.36% | 97.26% |
| 2026 | 131 | 75.19% | 87.60% | 98.45% |

The normalized fresh trigger is materially more stable across years than the original fixed-$10 fresh75 trigger.

## 9. Original fixed-$10 fresh75 explains its own drift

For the existing fixed-$10 fresh75 population:

```text
2025 N342
2026 N603
```

Actual 15m fixed-$10 hit:

```text
2025 52.68%
2026 77.03%
```

But actual 15m `1.25 ATR` hit on the same triggers:

```text
2025 61.31%
2026 62.67%
```

The trigger-time median ATR differed substantially between years, so a $10 target did not represent a comparable move.

This directly supports volatility normalization as a target-design issue, not merely an exit tweak.

## 10. Fixed-$10 fresh75 payoff exploration

This section is a development control, not the new normalized strategy.

Keep the existing fixed-$10 fresh75 trigger and the previously developed mandatory direction engine. Keep SL=$10 and vary TP.

| TP | Nominal payoff | 2025 WR | 2026 WR | 2025 EV | 2026 EV |
|---:|---:|---:|---:|---:|---:|
| $10 | 1.00R | 59.65% | 58.87% | +0.193R | +0.177R |
| $12 | 1.20R | 54.09% | 54.56% | +0.190R | +0.200R |
| $12.5 | 1.25R | 52.92% | 53.40% | +0.191R | +0.201R |
| $13 | 1.30R | 52.63% | 52.07% | +0.207R | +0.198R |
| $13.5 | 1.35R | 50.88% | 50.75% | +0.192R | +0.193R |
| $14 | 1.40R | 50.58% | 49.92% | +0.210R | +0.198R |
| $15 | 1.50R | 50.00% | 47.93% | +0.243R | +0.198R |

Development interpretation:

- approximately 1.20R-1.35R is a broad positive payoff plateau;
- 1.30R is the central robust comparison candidate;
- 1.35R is the observed upper boundary where both years still remained above 50% WR;
- neither value has promotion authority;
- 2025/2026 are already consumed for this branch.

Do not fine-tune 1.31/1.32/etc.

## 11. Why simply replacing the exit with ATR did not solve the old strategy

Changing only the exit to ATR units while retaining an entry trigger trained on the fixed-$10 movement target did not produce a major improvement.

This is an information-contract mismatch:

```text
entry asks: high probability of fixed $10 movement
exit asks: ATR-normalized movement
```

Therefore the next strategy must normalize the entire chain, not only the stop/target.

## 12. Retained conclusion

Retain V8-A-N as a research challenger because:

1. normalized movement base rates are highly stable across 2022-2026;
2. normalized excursion distributions are highly stable;
3. normalized fresh-high triggers show strong and stable realized movement rates;
4. the result directly addresses the fixed-$10 regime-difficulty problem.

Do not promote it because:

1. normalized AUC is lower than fixed-$10 A2;
2. distance monotonicity is not structurally guaranteed in the current prototype;
3. no normalized-trigger direction engine has yet been developed;
4. ATR-consistent entry/SL/TP economics have not yet been compared as a complete strategy;
5. no MT5/Python parity or execution validation exists for V8-A-N.

## 13. Next research contract

The immediate next research is:

### Stage N1 — freeze normalized movement trigger family
Compare 1.25ATR, 1.50ATR and 2.00ATR fresh-75 populations using outcome-blind/structural criteria:

- movement precision;
- sample count;
- year stability;
- signal clustering;
- ATR distribution;
- session distribution.

Do not select a trigger because its eventual direction P/L is best.

### Stage N2 — direction engine on the frozen normalized-trigger population
Build direction predictors specifically for the new population.

Do not assume the old fixed-$10 fresh75 direction engine transfers.

Direction research should separately test:

- price/candle/MTF state;
- partial HTF geometry;
- signed activity/tick pressure;
- liquidity/structure;
- new-information sources if needed.

No abstention merely to inflate WR unless a selective strategy is explicitly opened as a separate research target.

### Stage N3 — ATR-consistent risk/payoff
After direction is frozen, test SL/TP in the same normalized units.

Examples:

```text
SL 1.00 ATR / TP 1.00 ATR
SL 1.00 ATR / TP 1.25 ATR
SL 1.00 ATR / TP 1.50 ATR
```

The exact family must be preregistered before economics are opened.

### Stage N4 — complete strategy comparison
Compare:

1. existing fixed-$10 fresh75 control;
2. fixed-$10 fresh75 + 1.30R development payoff control;
3. normalized fresh trigger + normalized direction engine + ATR-consistent SL/TP.

Report by year:

```text
N
WR
average winner R
average loser R
EV/trade
PF
DD
loss streak
holding time
trade clustering
cost sensitivity
```

GOLD# 2021 remains locked.

## 14. Artifacts

Compact audited tables are stored in:

`docs/ea/v8/results/v8_a_n_20260901/`

Prototype coefficient packs are stored in:

`config/v8_a_n_models_20260901/`

Large all-M5 probability ledgers are intentionally not committed in this update.
