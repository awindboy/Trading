# V6-003D Role-Conditioned Core Freeze Results

Status: `RESEARCH RESULT / CORE FREEZE`
Date: `2026-08-29`
Expected base HEAD: `8f9c6e3e03906f2e8b4c146c3b3bb4741f6ad0e2`
Production authority: `NONE`
Consumed research panel: `13 market-years`
Untouched reserve: `GOLD 2021`

## 1. Executive result

After the directional-prior atlas, the research regressed from named indicators to role-specific physical horizons, local negotiation path, destination state, execution and market suitability.

The current parsimonious research control is:

```text
H  = DIRECT + D24 aligned + MENV HIGH_HIGH
L1 = DIRECT + D14=D24=local, excluding H-authorized parents
L2 = ONE_RENEG + D24 aligned
```

Combined consumed-panel result:

```text
253 trades
WR 54.55%
avg positive +1.269R
EV +0.304R
net +76.96R
historical max DD about 9.37R
11/13 market-years positive
```

This does not meet the final average-positive target of >=2R and therefore is not a production strategy.

## 2. Research-panel allocation

```text
GOLD    2022 / 2023 / 2024 / 2025
BTCUSD  2023 / 2024 / 2025
USDJPY  2023 / 2024 / 2025
XAUEUR  2023 / 2024 / 2025
```

All 13 are consumed discovery/falsification evidence.

Short extra-market diagnostics exist for XAUJPY/XAUCNH/GAUCNH/GAUUSD from roughly 2025-09 to 2025-12. These are too short and too correlated to count as independent validation.

## 3. Critical methodological corrections

### 3.1 Active-market clock

Previous wall-clock first-passage calculations were distorted by market closures/weekends.

Recomputed active-hour first-passage medians across direct fills:

```text
+1R  ~2.00h
+3R  ~7.64h
+5R  ~22.88h
SL   ~3.09h
```

Role separation:

```text
L: about 2-4 active hours
H: about 8-48 active hours
```

### 3.2 Market base rate

Raw LONG/SHORT accuracy was adjusted against market-year endpoint base rate. Some apparent SHORT failure was a market drift artifact. Direction research must not interpret raw hit-rate without this control.

### 3.3 M1 look-ahead

Conditioning a first M1 flip on the future fact that no later flip occurs before M5 trigger is look-ahead. All such early-M1 results were discarded.

### 3.4 Stable event keys

Separately sorted ledgers must be joined by stable event identity, not row index. Exact-key joining corrected MENV/H state alignment.

### 3.5 Timeframe vs physical horizon

Equal 24-bar displacement on M30/H1/H4 means 12h/24h/96h physical lookbacks. When physical lookback is fixed near 24 active hours, M15/M30/H1/H4 representations are broadly similar.

Conclusion: the H clue is approximately 24 active-hour displacement/persistence; `H1` is not itself the optimized causal object.

### 3.6 Direction vs execution

Chart-direction labels must exclude spread/slippage. A later FVG audit found that execution-adjusted direction labels can create false 52-54% directional effects when the underlying chart move is small.

## 4. Core module definitions and economics

### 4.1 H — large destination

Definition:

```text
M1 path = DIRECT
D24 = local direction
MENV state = HIGH_SCALE & HIGH_ACCEPTANCE
Entry = existing 50% trigger/broken-M5 pullback
SL = sweep extreme
+3R -> realize 25%
residual -> BE
+5R -> final
```

Result:

```text
N 51
positive 21
WR 41.18%
avg positive +3.786R
EV +0.971R
net +49.50R
```

Lifecycle breakdown:

```text
21 SL before +1R
9 SL after +1R but before +3R
4 BE after +3R
17 TP5
```

Approximate holding:

```text
SL median ~3.9 active h
TP5 median ~41.1h
BE median ~66.3h
```

Median initial risk: about `0.284 D1 ATR`.
Median +3R destination: about `0.851 D1 ATR` from Entry.
Median +5R destination: about `1.419 D1 ATR`.

Interpretation: H is a payoff module, not a high-hit-rate module. Time-impatience rules are dangerous because large winners can start slowly.

### 4.2 L1 — synchronized continuation

Definition:

```text
M1 path = DIRECT
D14 = D24 = local direction
parent is not H-authorized at trigger
Entry = next-M1 market execution
SL = sweep extreme
TP = +1R
maximum hold = 4 active hours
```

Result:

```text
N 76
WR 57.9%
EV +0.147R
net about +11.15R
```

Approximate holding:

```text
positive median ~2.19h
non-positive median ~1.53h
```

Median risk about `0.157 D1 ATR`.

### 4.3 L2 — negotiated resumption

Definition:

```text
pre-sweep M1 owner opposite event
then M1 ownership changes:
  event -> opposite -> event
exactly one renegotiation before M5 trigger
D24 = local direction
Entry = market
SL = sweep extreme
TP = +1R
maximum hold = 4 active hours
```

Result:

```text
N 126
WR 57.9%
EV +0.129R
net about +16.30R
```

Winner/loser holding medians are both near `1.8h`, so simple time-to-resolution is not a quality discriminator.

Median risk about `0.189 D1 ATR`.

## 5. Market-year core results

| Environment | N | WR | EV | Net R | Main interpretation |
|---|---:|---:|---:|---:|---|
| BTCUSD 2023 | 37 | 54.1% | +0.117 | +4.33 | thin L, positive core |
| BTCUSD 2024 | 18 | 33.3% | -0.188 | -3.38 | L direction/path failure |
| BTCUSD 2025 | 34 | 70.6% | +0.672 | +22.86 | strong multi-module year |
| GOLD 2022 | 20 | 60.0% | +0.432 | +8.64 | positive |
| GOLD 2023 | 17 | 41.2% | +0.297 | +5.06 | H payoff offsets low WR |
| GOLD 2024 | 13 | 53.8% | +0.362 | +4.71 | positive |
| GOLD 2025 | 12 | 50.0% | +0.561 | +6.73 | positive |
| USDJPY 2023 | 14 | 71.4% | +0.542 | +7.59 | positive |
| USDJPY 2024 | 21 | 61.9% | +0.347 | +7.29 | positive |
| USDJPY 2025 | 9 | 55.6% | +0.270 | +2.43 | low density, positive |
| XAUEUR 2023 | 16 | 43.8% | +0.149 | +2.39 | positive |
| XAUEUR 2024 | 18 | 66.7% | +0.648 | +11.66 | strong |
| XAUEUR 2025 | 24 | 37.5% | -0.139 | -3.33 | H destination failure |

The two negative environments fail for different reasons. Do not create one universal bad-regime filter.

## 6. L direction and lifecycle research

### 6.1 L1 relation

The simple L1 direction candidate was `D14=D24=local`.

Broad 4h direction accuracy was about two-thirds before exact execution monetization. L1 generated a real short-lived edge; 4h cap materially outperformed letting the 1R/SL race run indefinitely.

### 6.2 L1 exit frontier

Controls included:

```text
+1R / 4h cap
pure 4h hold
50% @ +1R + residual 4h
50% @ +1R + residual BE
+1R then +0.5R lock
midpoint fast/slow routing
```

The frontier was real:
- 1R harvest preserves WR but keeps avg winner small;
- pure 4h hold improves EV/payoff but lowers WR;
- intermediate compromises did not simultaneously solve both targets.

No nearby fraction/hour optimization is authorized.

### 6.3 L2 discovery

The non-direct population contained a large exact `event -> opposite -> event` path family. This ONE_RENEG path was near breakeven unconditionally but became positive when D24 agreed with the final local event.

Original L2 D24-aligned result remained more defensible than the later `D14 OR D24` density extension because the D14-only branch was too thin/cost-sensitive.

### 6.4 L2 D24-age clue

Consumed-panel split:

```text
fresh age <24 H1 bars:
N84 / WR 48.8% / EV ~+0.003R

mature age >=24 H1 bars:
N42 / WR 76.2% / EV ~+0.381R
```

Continuous age remained positively related to PnL under several controls. However:
- GOLD recurrence is inconsistent;
- short external sample has only 4 mature trades;
- correlated gold crosses cannot count as independent proof.

Status: `SHADOW / EXTERNAL-VALIDATION CANDIDATE`.

A mature-L2 `+1R survival -> BE -> +3R within 4h` lifecycle improved consumed-panel EV, but it is not promoted.

## 7. H research and closure

The following H extensions were tested and rejected/degraded:

- opposed-H automatic inversion;
- D14 reversal-transition rescue;
- 4h +1R survival checkpoint;
- D24 mature non-HH promotion;
- mixed MENV quadrants as +3R H;
- super-HH continuous score/margin;
- simple scale/acceptance strength ranking inside HH;
- L1->H survival hybrids as final architecture.

Reason: either they cut slow large winners, dilute edge, or fail environment recurrence.

Current H is binary destination authority. Do not keep optimizing HH strength on the same panel.

## 8. Trade-count research

### 8.1 Raw source is not the final bottleneck

The k=2 M15 DC source creates enough raw opportunity. Final density falls through:

```text
DC level
-> atomic same-M1 sweep/recovery
-> valid M5 structural transition
-> M1 path quality
-> direction/destination authorization
```

### 8.2 Recovery->M5 conversion

Approximate consumed-market aggregate:

```text
BTCUSD 16.6%
GOLD   11.2%
USDJPY 11.0%
XAUEUR 11.9%
```

This conversion is strongly associated with annual L trade count (roughly Spearman rho 0.86) but not reliably with L EV or WR.

Interpretation: `density descriptor`, not profitability filter.

### 8.3 Core annual density

Approximate core trades/year:

```text
BTCUSD ~29.7
GOLD   ~15.5
USDJPY ~14.7
XAUEUR ~19.3
```

This remains below the user's desired practical frequency on several markets.

The research did not lower quality gates merely to hit one trade/week.

## 9. Alternative event/source research

The project explicitly questioned whether the M15 DC event only looked best because its downstream pipeline had been designed around it.

Therefore alternative event sources were explored with source-specific or neutral pipelines.

### 9.1 Failed/degraded source families

- M5 liquidity source: very high N, negative economics.
- previous completed H4 high/low: high N, negative broad economics.
- PDH/PDL: some mean-reversion-like cells, insufficient robust/cost-adjusted promotion.
- M15 confirmed pivots: high N, weak/negative current-rule transfer.
- opening-range source: negative broad economics.
- accepted breakout/retest: negative direction/economics.
- delayed failed breakout: negative.
- M15 BOS retest: negative direction and economics.
- generic pullback-resumption without liquidity source: high N, negative.

### 9.2 Multi-scale M15 DC

Frozen legacy scales k=1.5/2/2.5 were unioned physically. Extra k=1.5/2.5 events increased density but diluted L economics. M30 DC mostly rediscovered the same physical good events rather than adding independent opportunities.

Conclusion: k=2 remains the current source control; do not call it universally optimal.

## 10. FVG research closure

FVG received event-specific treatment after the event-definition critique.

Research included:
- M15/H1 FVG;
- REJECT / INSIDE / ACCEPT body-close states;
- CE/midpoint geometry;
- freshness, gap width, displacement, stacked zones;
- volume/activity proxies;
- matched non-event candle controls;
- boundary-reversion, time-exit and ATR-stop economics.

Two important corrections invalidated earlier favorable-looking numbers:

1. overlapping FVG zones were duplicated by insufficient merge identity;
2. direction labels had execution spread embedded and had to be rebuilt chart-only.

After correction:
- M15 FVG provides little independent direction information;
- much movement uplift is explained by already-large confirmation candles;
- H1 FVG has only a small location-specific tilt;
- broad cost/path economics remain negative/thin.

Decision: `FVG RESEARCH CLOSED`.

## 11. Execution / cost findings

Median spread / initial R:

```text
H  ~2.8%
L1 ~6.3%
L2 ~4.7%
```

BTC L spread/R is materially larger than the panel average.

Illustrative chart-to-spread drag is especially relevant for BTC L2. Some weak environments remain negative even chart-only, proving that not all failures are execution-only.

H has more cost headroom but often holds 24-72+ active hours, so swap/overnight financing is mandatory in the next execution stage.

## 12. Robustness and concentration

13-market-year block Monte Carlo / bootstrap, preserving within-block trade order:

```text
combined EV 2.5%  ~ +0.14R
median             ~ +0.304R
97.5%              ~ +0.47R
```

Module-level uncertainty is wider for L1/L2 and stronger for H.

Net contribution approximately:

```text
H  +49.5R  (~64%)
L1 +11.15R (~15%)
L2 +16.30R (~21%)
```

Positive-R concentration is not dominated by one or two jackpot trades.

## 13. Exposure shadow

Same-market live-position overlap is rare in the frozen 253-trade core. Opposite-direction same-market overlap was observed only rarely in the historical replay.

This does not eliminate the need for portfolio/exposure rules, but exposure collision is not currently the main strategy bottleneck.

## 14. Short external-market diagnostics

Short histories:

```text
XAUJPY
XAUCNH
GAUCNH
GAUUSD
```

show different recovery->M5 conversion and spread/R profiles. XAUCNH/GAUCNH appear denser in the short sample, but they are correlated gold/CNH expressions and must not be counted as independent proof.

No warmup/rule was relaxed to manufacture external N.

## 15. Closed attempts summary

Do not reopen by nearby threshold rescue:

```text
conventional indicator atlas
owner coherence as required L gate
first-M1 direct look-ahead result
automatic H opposed inversion
H time impatience
H super-score
non-HH +3R routing
L2 50% pullback Entry
D48 rescue for fresh L2
M1 renegotiation-duration gate after composition test
M5 trigger weakening
multi-scale source dilution
M5/H4/pivot/OR/FVG alternative-source proliferation
accepted-breakout and failed-break families
generic pullback without event quality
```

## 16. Next development direction

Do not continue consumed-panel micro-tuning by default.

### Phase A — outcome-blind market breadth

1. obtain longer XAUJPY/XAUCNH/GAUCNH/GAUUSD histories;
2. add non-gold-like candidate markets;
3. compute source density, recovery->M5 conversion, spread/R and session coverage before P/L;
4. freeze market shortlist;
5. then open strategy outcomes.

### Phase B — frozen-core validation

Run unchanged H/L definitions on the frozen shortlist.
Report module N, WR, avg positive R, EV, DD, loss streak, market/year/direction breadth and contribution concentration.

### Phase C — shadow hypothesis validation

Validate L2 D24 age unchanged. Do not retune the 24-bar boundary.
Only if it survives independent data may the mature runner lifecycle be considered.

### Phase D — execution

For L:
- exact spread;
- commission;
- slippage;
- market vs pending semantics.

For H:
- same plus swap/overnight financing;
- long-hold session gaps;
- exact pending fill parity.

### Phase E — MT5 / EA

Only after external and execution evidence:
- implement research shadow first;
- OFF/ON parity;
- Every tick based on real ticks where possible;
- compare identical baseline/control conditions;
- preserve scenario/Entry/SL/TP semantics exactly.

## 17. Freeze statement

The 253-trade role-conditioned core is the comparison control for the next phase.

It is not the final strategy. It is the point at which further same-panel rule invention is more likely to overfit than to advance the project.
