# V6-003A Directional Prior Research Results

Status: `FIRST ATLAS CLOSED / EXTERNAL VALIDATION CANDIDATE ONLY`  
Date: `2026-08-29`  
Base GitHub HEAD: `982839b0a1ea166fc534272f2024a72cedfb8326`  
Production authority: `NONE`  
Control: `MENV-004`  
Untouched reserve: `GOLD 2021`

## 1. Executive verdict

The first directional-prior atlas does **not** justify a new strategy.

1. **P1 H1 DMI14 direction is closed as an independent directional prior.**
2. **P2 H1 24-bar signed displacement is stronger than P1**, but is weak/asymmetric over the full 620-opportunity panel.
3. A more specific interaction survives falsification better:

```text
existing MENV HIGH_SCALE AND HIGH_ACCEPT
+
P2 aligned with the later local event
```

This looks like a **cross-scale continuation-capacity state**, not a DMI edge.
4. This interaction is still consumed-panel evidence. It is negative on XAUEUR in market aggregate, has only 51 P2-aligned accepted MENV trades, and does not meet the final WR requirement.
5. `P2 OPPOSED -> trade the P2 direction after local failure` was explicitly falsified.
6. Therefore **no routing strategy is frozen in V6-003A**. P2 x HIGH_HIGH is retained only as an external-validation candidate.

## 2. Exact MENV-004 parity regression

Before opening directional-prior outcomes, the raw replay was required to reproduce the current benchmark.

### Correct D1 initialization

The correct rule comes from the committed V3 code:

```text
D1 = calendar resample
ATR14 = rolling completed D1 bars
availability = D1 bar open + 1 day
```

No arbitrary deletion of a first “partial” D1 bar is permitted.

D1-valid direct opportunities:

| Segment | Raw direct | Causal D1-valid |
| --- | ---: | ---: |
| GOLD 2022 | 52 | 51 |
| GOLD 2023-2025 | 119 | 117 |
| BTCUSD 2023-2025 | 215 | 213 |
| USDJPY 2023-2025 | 117 | 115 |
| XAUEUR 2023-2025 | 125 | 124 |
| **Total** | **628** | **620** |

### Pending-order replay correction

A second scratch-replay bug allowed the MENV pending limit to fill on the M1 bar whose timestamp equaled `trigger_time`.

The frozen V3 implementation begins the pending search with:

```python
searchsorted(trigger_time, side="right")
```

so only the first M1 strictly after the trigger can fill.

After correcting this, replay parity became exact:

```text
620 broad-direct causal-valid
540 MENV state-valid
163 HIGH_HIGH parents
151 fills
7 opposite-direction exposure blocks
144 accepted
48 positive
total +71.25R
EV +0.4947916667R
```

All 13 market-year N / TP5 / BE / SL / total-R rows match `V6_MENV004_BY_ENV.csv`.

## 3. Pre-outcome atlas density

Across all 620 causal opportunities:

| Prior | ALIGNED | OPPOSED | NEUTRAL |
| --- | ---: | ---: | ---: |
| P1 H1 DMI14 | 202 | 418 | 0 |
| P2 H1 DISP24 | 220 | 400 | 0 |
| S1 H1 BOS | 223 | 397 | 0 |
| S2 M30 BOS | 166 | 454 | 0 |
| S3 H1/M30 concordant | 119 | 350 | 151 |

P1 and P2 point in the same absolute direction on **84.52%** of opportunities.

This high overlap is an important simpler-explanation warning: favorable P1 behavior must survive comparison with simple price displacement.

## 4. Full 620-opportunity raw path

The same frozen 50% pullback geometry produced:

```text
620 opportunities
586 fills
273 reached +1R before original structural stop
138 reached +3R
94 reached +5R
```

### P1 — H1 DMI14

| State | Fill N | +1R | +3R | +5R |
| --- | ---: | ---: | ---: | ---: |
| ALIGNED | 192 | 46.88% | 24.48% | 16.15% |
| OPPOSED | 394 | 46.45% | 23.10% | 15.99% |

P1 is essentially flat in the broad population.

When P1 and P2 disagree, P2 is materially stronger:

```text
P1 aligned / P2 opposed: 35 fills
+1R 40.0% / +3R 14.3% / +5R 8.6%

P2 aligned / P1 opposed: 53 fills
+1R 50.9% / +3R 26.4% / +5R 20.8%
```

**Verdict: close P1 as an independent directional edge.**

### P2 — H1 DISP24

| State | Fill N | +1R | +3R | +5R |
| --- | ---: | ---: | ---: | ---: |
| ALIGNED | 210 | 49.05% | 26.67% | 18.57% |
| OPPOSED | 376 | 45.21% | 21.81% | 14.63% |

This is directionally favorable, but not strong enough to promote:

- environment recurrence remains mixed;
- cluster-bootstrap intervals cross zero for +1R/+3R/+5R;
- broad effect is strongly SHORT-concentrated;
- LONG broad P2 aligned vs opposed is nearly flat.

Therefore P2 alone is not a portable direction authority.

## 5. Existing MENV-004 state interaction

The pre-existing MENV HIGH_HIGH state was frozen before V6-003A and is not an outcome-derived threshold.

Within its **151 filled parents**:

| P2 state | N | +1R | +3R | +5R |
| --- | ---: | ---: | ---: | ---: |
| ALIGNED | 53 | **58.49%** | **41.51%** | **35.85%** |
| OPPOSED | 98 | 50.00% | 28.57% | 19.39% |
| Difference |  | +8.49pp | +12.94pp | +16.46pp |

The +5R difference is positive in 11/13 market-years. Restricting descriptively to cells where both sides have at least three fills gives 9 positive / 1 negative.

Market aggregate +5R aligned-minus-opposed:

```text
BTCUSD +26.15pp
GOLD   +20.11pp
USDJPY +18.05pp
XAUEUR  -2.75pp
```

LONG and SHORT are both positive in the pooled HIGH_HIGH subset:

```text
SHORT +5R delta +26.63pp
LONG  +5R delta  +9.20pp
```

Fixed-clock behavior is also directionally consistent in the pooled subset:

```text
48h median MFE:
P2 aligned 0.715 D1 ATR
P2 opposed 0.570 D1 ATR

48h median MAE:
P2 aligned 0.414 D1 ATR
P2 opposed 0.595 D1 ATR
```

## 6. Falsification and uncertainty

### Cluster bootstrap by market-year

Resampling the 13 environment clusters with replacement:

| Metric | Observed delta | 95% cluster interval |
| --- | ---: | ---: |
| +1R | +8.49pp | -6.61pp to +26.80pp |
| +3R | +12.94pp | -3.00pp to +28.19pp |
| +5R | +16.46pp | **+0.18pp to +33.16pp** |

Only +5R barely excludes zero.

### Stratified label permutation

Within exact `market-year x local-event direction` strata, preserving P2-aligned counts:

| Metric | One-sided p | Two-sided p |
| --- | ---: | ---: |
| +1R | 0.271 | 0.381 |
| +3R | 0.216 | 0.221 |
| +5R | **0.061** | **0.061** |

This is suggestive, not decisive.

### Residual MENV-strength confound

Within HIGH_HIGH fills, P2-aligned events also have somewhat larger continuous scale/acceptance values. Sparse nearest-neighbor matching reduces but does not erase the +5R difference.

Therefore the evidence supports a **candidate interaction**, not a proven causal P2 effect.

## 7. Exact MENV accepted-trade comparison

After the frozen exposure rule, MENV-004 remains 144 accepted trades.

P2 split:

| P2 state | N | Positive | WR | Avg positive R | EV | Total R |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ALIGNED | 51 | 21 | 41.18% | 3.786R | +0.971R | +49.50R |
| OPPOSED | 93 | 27 | 29.03% | 3.250R | +0.234R | +21.75R |

This is economically interesting but **not a strategy pass**:

- WR is still below 50%;
- N would collapse from 144 to 51 under a simple aligned-only veto;
- the project explicitly forbids hiding a trade-count problem behind high EV.

## 8. Opposite thesis / inversion test

A separate diagnostic tested the tempting interpretation:

```text
P2 OPPOSED + strong local HIGH_HIGH reaction
-> local reaction fails
-> price should resume in the P2 prior direction
```

For 79 HIGH_HIGH P2-opposed structural failures, measured from the first M1 after the local structural stop:

```text
24h prior-direction endpoint median = -0.044 D1 ATR
24h endpoint-positive rate          = 45.6%
48h endpoint median                 = +0.013 D1 ATR
48h endpoint-positive rate          = 50.6%
```

24h market endpoint medians are negative in BTCUSD, GOLD and XAUEUR; only USDJPY is clearly positive.

**Verdict: no automatic `OPPOSED -> opposite-direction H` or post-failure inversion branch.**

## 9. Mechanism interpretation

The surviving observation is narrower than “trend works”:

> When an already-large, strongly accepted local reaction points in the same direction as a simple completed-H1 displacement prior, that reaction appears more capable of continuing to distant +3R/+5R destinations.

This is best named **cross-scale continuation capacity**.

The evidence does **not** support:
- DMI as special directional information;
- P2 as a universal pre-event trade direction;
- automatic trading against the local event when P2 is opposed;
- an aligned-only 51-trade strategy.

## 10. Decision

### Closed

```text
P1 H1 DMI14 as independent directional prior
P2 as standalone universal direction authority
OPPOSED -> prior-direction inversion
```

### Retained only for future validation

```text
P2 H1 DISP24
x
pre-existing MENV HIGH_SCALE AND HIGH_ACCEPT
->
cross-scale continuation-capacity hypothesis
```

No threshold/window/market-specific rescue is allowed.

No production change.

No GOLD 2021.

No consumed-panel routing strategy is frozen.

## 11. Exact next research step

The next evidence must come from **new or longer outcome-blind environments**, not more slicing of the same 13 consumed market-years.

Priority:

1. acquire longer XAUJPY / XAUCNH / GAUCNH / GAUUSD histories so the frozen 20-prior MENV baseline can initialize;
2. add other outcome-blind markets only under a frozen universe rule;
3. before opening their outcomes, freeze the exact P2 x HIGH_HIGH validation hypothesis and no-rescue criteria;
4. require recurrence by market/period and direction;
5. only after validation may one routing architecture be preregistered.

The short 2025 GoldLike2 histories remain unusable for this validation because none reaches the 20-prior-opportunity warmup.

## 12. Source lineage

Core repository sources:
- `scripts/v3_003c_reload_state_acceptance_probe.py`
- `scripts/v3_003d_correction_completion_probe.py`
- `scripts/v3_003e_dual_module_repro.py`
- `scripts/v6_001b_indicator_atlas.py`
- `docs/ea/v6/V6_003A_DIRECTIONAL_PRIOR_RESEARCH_CONTRACT.md`
- `docs/ea/v6/ledgers/V6_MENV004_BY_ENV.csv`

Literature mechanism references:
- Moskowitz, Ooi, Pedersen (2012), *Time Series Momentum*, Journal of Financial Economics.
- Kim, Tse, Wald (2016), *Time Series Momentum and Volatility Scaling*, Journal of Financial Markets.
- Hurst, Ooi, Pedersen (2017), *A Century of Evidence on Trend-Following Investing*.
- Daniel, Moskowitz (2016), *Momentum Crashes*, Journal of Financial Economics.

The literature supports treating trend persistence as a plausible prior while separately guarding against volatility-scaling confounds and regime-dependent momentum failure; it does not validate this strategy-specific result.
