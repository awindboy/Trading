# V10 R6/R7 ML Sizing and Raw-M1 Economic Checkpoint — 2026-09-17

Date: `2026-09-17`
Status: `CONSUMED-DATA SHADOW RESEARCH / NO STRATEGY OR EA PROMOTION`
Market: `GOLD# ONLY`
Base GitHub HEAD: `aa7685b9e243ddff058f0dbcdb8e416260b41244` (`update V10 R4,5`)

## 1. Why this checkpoint exists

R4/R5 established useful specialist signals, but the next problem was not simply to add more ML.
The central question became:

> Can the existing HA participation structure place **more exposure only when the current opportunity and the recent market environment both justify it**, without trying to predict the next HA color directly?

The key negative conclusion is important:

```text
preceding HA / MTF flow contains context
!=
reliable direct prediction of the next HA state across Gold regimes
```

Direct next-step / survival-style signals can be statistically learnable, but their economic meaning changes materially across liquidity regimes. The more robust use of ML so far is therefore **participation sizing / exposure placement**, not replacing the H4 FAST HA campaign clock or claiming deterministic next-HA prediction.

## 2. Data / causality contract

Authoritative raw source:

```text
GOLD#_M1_202201030100_202608282357.csv
SHA256 626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2
```

The R7 M1 audit used the same raw-M1 source lineage as R3.
No 2021 data were unsealed.

Causality preserved:

- no future HA bar is visible before completion;
- final FAST run length `L` is label/audit only;
- realized Child R/PnL is never a live model feature before the Child exits;
- stopped Children remain dead;
- R7 feedback uses only already-exited prior Children;
- no hindsight Child insertion after later price reveal.

## 3. R6 — what was tried and rejected

R6 tested whether R4/R5 specialist outputs could be combined into a more general meta-alpha.
Gold liquidity heterogeneity was handled with fixed quarter samples rather than one pooled annual score.

### 3.1 Direct realized-R meta

Rejected.
It learned a large amount of STOP avoidance but failed to preserve the economically important right tail.
High rank correlation did not imply better trading economics.

### 3.2 Right-tail classification

A 2024-developed `R >= 3R` specialist did not generalize stably to 2025/2026 sampled quarters.
The failure was regime-dependent rather than a simple model-family issue.

### 3.3 Causal relative-rank / percentile normalization

A trailing causal relative representation did not outperform raw evidence.
Gold regime migration is therefore not just a scale-normalization problem; the mapping from state to outcome itself changes.

### 3.4 Downside + right-tail meta

The meta retained more 3R+/5R winners, but stop/severe-loss exposure rose materially and DD worsened.
The model learned convex opportunity but did not price the downside/campaign cost reliably.

### 3.5 Generic exposure downgrade

Generic `3 -> 1` downgrade models reduced DD mostly by removing exposure and sacrificed too much R.

### 3.6 R6 conclusion

Under the fixed sampled-quarter contract, none of R6B-R6F beat R4.
R4 remained the best R4/R5-family baseline.

The important research lesson was:

```text
more ML heads
!=
better economic interpretation

next-HA / survival predictability
!=
stable sizing edge
```

## 4. R7 — changing the ML role

R7 stopped asking ML to replace the core HA trade structure.
Instead, it asked a narrower question:

> R4 already says this Child deserves 1 unit. When is it justified to upgrade that existing Child from 1 unit to 3 units?

No new entry is created.
No R4-selected trade is removed by the core R7G rule.
No exit rule changes.

### 4.1 Failed R7 branches

The following were tested and rejected as primary candidates:

- regime-interaction k1 STOP abstention;
- direct right-tail upgrade without recent economic feedback;
- global regime-EV model;
- local regime mixture alone;
- global/local dual evidence without stable economics;
- OOD suppression;
- stage/direction-fragmented feedback;
- short-run damage classifier;
- exponential half-life feedback;
- hard regime-distance weighting.

Common failure mode:

```text
classification / probability quality can improve
while sizing economics still worsen
```

## 5. R7G core shadow hypothesis

The first candidate that remained positive across the predeclared sampled quarters was:

```text
population:
R4 current weight == 1

upgrade condition:
R5 EV > 0
AND
mean realized R of eligible already-exited prior Children
within the most recent 180 completed H4 bars > 0

then:
1 unit -> 3 units

else:
keep the original 1 unit
```

Important semantics:

- `180 H4` reuses the existing V10 H4 era-scale horizon; it is not promoted as a permanent threshold;
- feedback uses already realized prior outcomes only;
- it is a sizing shadow, not entry authority;
- R4 remains the base participation decision.

## 6. Sampled-quarter result

Original fixed sampled quarters:

| Quarter | Incremental R from R7G upgrade |
|---|---:|
| 2024 Q4 | +10.98R |
| 2025 Q2 | +6.69R |
| 2025 Q4 | +53.73R |
| 2026 Q1 | +69.74R |
| 2026 Q2 | +0.47R |

All five were positive.

Aggregate on that sampled set:

```text
R4 baseline      286.67R
R7G              428.28R
Delta           +141.61R
PF_R        1.485 -> 1.571
DD_R       50.43 -> 59.71
R/DD        5.68 -> 7.17
```

Run-block bootstrap:

```text
observed delta +141.61R
95% interval   [+18.05R, +288.75R]
P(delta > 0)   ~99.1%
```

This is encouraging consumed-data evidence, not independent validation.

## 7. Frozen-policy all-quarter diagnostic

Without changing the R7G rule after the sampled-quarter study, the same fixed policy was passed through all available quarters from 2024 Q4 through partial 2026 Q3 as an additional diagnostic.

Incremental R:

```text
2024 Q4  +10.98R
2025 Q1  +50.53R
2025 Q2   +6.69R
2025 Q3  +35.26R
2025 Q4  +53.73R
2026 Q1  +69.74R
2026 Q2   +0.47R
2026 Q3* +28.54R
```

`2026 Q3*` is partial through 2026-08-28.

Aggregate:

```text
R4      485.07R
R7G     741.01R
Delta  +255.94R
PF_R    1.583 -> 1.682
DD_R   50.32  -> 59.71
R/DD    9.64  -> 12.41
```

Run-block bootstrap 95% interval for the frozen-policy diagnostic was approximately:

```text
[+101.92R, +435.63R]
```

The diagnostic quarters are consumed evidence and are not a new validation set.

## 8. What the R7G edge actually looks like

The upgrade does **not** mainly work by raising win rate.
It works by accepting recurring small/medium losses and increasing participation in long FAST runs.

For R7G incremental exposure:

```text
L1-2   -87.49R
L3-5   -17.84R
----------------
L1-5  -105.33R

L6-8   +74.21R
L9-11  +60.16R
L12+  +112.57R
----------------
L6+   +246.94R
```

Interpretation:

> The current edge is more consistent with **trend-paying regime detection / exposure scaling** than with accurate prediction of the next HA bar.

This is the key answer to the "can we know the next HA?" question:

```text
not reliably enough to use direct next-HA prediction as the main authority;
preceding flow still matters as context,
but the stronger current use is deciding how much exposure to carry when a run pays.
```

## 9. Raw-M1 price-path parity audit

The R7 economic ledger was independently checked against the authoritative M1 price path.

Results:

```text
non-stop Children:
2,182 / 2,182 open-to-open price PnL exact

stop Children:
658 / 658 first M1 SL-touch time matched ledger exit_time

gap/open stop cases:
8
```

The H4 feedback index was also rebuilt from raw M1 completed H4 bars and reproduced the existing R7G feedback values exactly under the implemented `exit_time < current decision` causal rule.

## 10. PnL unit clarification

The raw-M1 research builder defines:

```text
pnl = direction * (exit_price - entry_price)
```

Therefore the persisted `pnl` is **GOLD price movement / price-PnL**, not an MT5 account-currency profit figure.

Always distinguish:

```text
price-PnL
!=
structural R
!=
actual account-currency PnL
```

Actual account money additionally depends on stop distance, contract size, lot calculation, risk budget, execution cost and concurrent campaign risk.

## 11. M1-verified economic comparison

Across the M1-verified diagnostic population:

| Policy | Units | Structural R | PF_R | DD_R | Raw price-PnL | Spread-adjusted R | Spread-adjusted price-PnL |
|---|---:|---:|---:|---:|---:|---:|---:|
| R4 baseline | 3,095 | 485.07R | 1.583 | 50.32R | 23,234.65 | 463.89R | 22,590.76 |
| R7G all | 3,881 | 741.01R | 1.682 | 59.71R | 30,883.72 | 712.86R | 30,074.67 |
| R7G no-k3p-SHORT diagnostic | 3,815 | 754.42R | 1.711 | 57.97R | 30,194.87 | 726.75R | 29,397.62 |

The third row is a **post-hoc consumed-data refinement**, not a promoted successor to R7G.

## 12. Actual money decomposition of R7G incremental exposure

The raw price-PnL of the 393 upgraded Children decomposed as:

```text
166 winners  +15,602.22 price-PnL
227 losers    -7,953.15 price-PnL
net           +7,649.07 price-PnL
```

Run-length price-PnL decomposition:

```text
L1-2   -4,037.55
L3-5     -924.02
L6-8   +2,436.67
L9-11  +2,811.40
L12+   +7,362.57
```

Again, these are GOLD price-movement PnL units, not broker-account USD.

## 13. Direction / stage diagnostic

The most notable post-hoc weakness was `k3p SHORT` incremental sizing:

```text
k3p SHORT upgrade:
raw price-PnL  +688.85
structural R   -13.41R
```

This means fixed-lot price movement and stop-normalized economics disagree.
The no-k3p-SHORT variant improved consumed-data structural R / PF_R / DD_R, but it was discovered after observing the same data and therefore remains diagnostic only.

Do not promote a hidden `no k3p SHORT` rule without independent evidence.

## 14. Spread and risk warnings

Using M1 spread as a cost stress reduced, but did not erase, the observed edge.

However max concurrent unit exposure reached:

```text
R4   40 units
R7G  48 units
```

The maximum R7G snapshot came from many Children within one long campaign, not necessarily many unrelated campaigns.

Therefore a naive statement such as `1 unit = 1% account risk` would imply an unacceptable nominal committed-risk interpretation at peak exposure.
No account return claim is valid until exact Child lot sizing and campaign committed-risk accounting are implemented.

## 15. Horizon stress

The 180-H4 feedback window is promising but not fully insensitive to the exact horizon.

```text
120 H4  total delta strongly positive, 6/8 diagnostic quarters positive
180 H4  total delta strongly positive, 8/8 positive
240 H4  total delta strongly positive, 7/8 positive
```

An exponential half-life alternative failed because strong old trend periods retained too much influence into a later weak regime.

Interpretation:

> The useful mechanism appears to require genuinely discarding stale regime economics, not merely downweighting them forever.

Still, `180` is not production authority.

## 16. Current research decision

Supported for continued shadow research:

```text
H4 FAST HA remains the campaign clock.
R4 remains the base participation model.
R7G is a sizing overlay only.
The useful ML role is exposure placement / recent economic feedback,
not direct next-HA prediction.
```

Not promoted:

```text
R7G as production sizing authority
180-H4 as a permanent threshold
no-k3p-SHORT as a rule
any new campaign risk cap
any direct next-HA predictor
```

All 2024-2026 evidence is consumed research evidence.
`GOLD# 2021` remains sealed unless a separate explicit validation contract releases it.

## 17. Next work

Freeze the R7G core semantics. Do not continue scanning the same consumed data for another threshold.

Next work order:

```text
1. persist exact R7G row-level reproducibility contract
2. Python/MQL feature + Boolean action parity
3. actual-tick-compatible sizing ledger
4. Child lot calculation from exact stop distance and account risk
5. campaign committed-risk accounting
6. forward-only shadow evidence after the current historical cutoff
7. only then consider authority promotion or a separately frozen reserve-validation contract
```
