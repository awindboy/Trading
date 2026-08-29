# V6 Research State

Status: `ACTIVE / RESEARCH CORE FROZEN`
Date: `2026-08-29`
Phase: `V6-003D ROLE-CONDITIONED CORE FREEZE / EXTERNAL VALIDATION PREP`
Production authority: `NONE`
Base HEAD for this documentation update: `8f9c6e3e03906f2e8b4c146c3b3bb4741f6ad0e2`
Untouched reserve: `GOLD 2021`

## 1. Consumed panel

```text
GOLD    2022-2025
BTCUSD  2023-2025
USDJPY  2023-2025
XAUEUR  2023-2025
```

13 market-years total. These are discovery/falsification data.

## 2. Frozen research control

| Module | Definition | N | WR | Avg positive | EV |
|---|---|---:|---:|---:|---:|
| H | DIRECT + D24 aligned + MENV HH | 51 | 41.18% | +3.786R | +0.971R |
| L1 | DIRECT + D14=D24=local, excluding H-authorized parent | 76 | 57.9% | ~+0.80R | +0.147R |
| L2 | ONE_RENEG + D24 aligned | 126 | 57.9% | ~+0.83R | +0.129R |
| Combined | causal H priority | 253 | 54.55% | +1.269R | +0.304R |

Combined net: about `+76.96R`; historical max DD about `9.37R`; positive market-years `11/13`.

## 3. Current interpretation

```text
D24 = directional authority
D14 = L1 short-horizon synchronization
M1 path = local negotiation quality
MENV = H destination authority
```

No stage variable currently substitutes for another.

## 4. Time-horizon result

Active-market first-passage analysis:

```text
+1R median about 2.0 active h
+3R median about 7.6 active h
+5R median about 22.9 active h
structural SL median about 3.1 active h
```

Role interpretation:

```text
L natural horizon: roughly 2-4 active hours
H natural horizon: roughly 8-48 active hours
```

H TP5 winners commonly need much longer than L and must not be subject to L-style impatience exits.

## 5. Physical-horizon correction

Equal lookback bar counts across TFs were previously confounded with different physical horizons.

When the H direction lookback is fixed near 24 active hours, M15/M30/H1/H4 representations are broadly similar. Therefore the durable H clue is `~24 active-hour displacement/persistence`, not “H1 is the optimized timeframe.”

For L, 14h+24h agreement plus smoothing is more important; raw M1 versions were weaker.

## 6. L2 maturity shadow

```text
D24 age <24 H1 bars:
N84 / WR 48.8% / EV ~+0.003R

D24 age >=24 H1 bars:
N42 / WR 76.2% / EV ~+0.381R
```

Status: `UNVALIDATED SHADOW`.

Maturity does not rescue noisy M1 paths and does not replace MENV for H.

## 7. Density / market-suitability state

The current M15 DC source can generate enough raw opportunity. Usable density is reduced mainly by the conversion chain.

Outcome-blind density descriptor:

```text
recovery -> valid M5 BOS transition rate
```

Consumed-panel aggregate approximate rates:

```text
BTC      16.6%
GOLD     11.2%
USDJPY   11.0%
XAUEUR   11.9%
```

This descriptor is strongly related to trade count, not reliably to profitability.

Short extra-market diagnostics:

```text
XAUJPY  about 10.6%
XAUCNH about 16.3%
GAUCNH about 18.0%
GAUUSD about 13.1%
```

These are short, correlated gold-like samples and are not independent validation.

## 8. Execution state

Median spread / initial R:

```text
H  ~2.8%
L1 ~6.3%
L2 ~4.7%
```

BTC L spread/R is materially higher than the panel average and can consume thin L gross edge.

H remains economically thicker but often holds overnight; swap must be included before production claims.

## 9. Failure decomposition

H 51-trade lifecycle:

```text
21 SL before +1R
9 SL after +1R but before +3R
4 BE after +3R
17 TP5
```

Once +3R is reached, continuation to +5R is strong. Do not re-open nearby profit-lock tuning.

Negative combined environments differ by module:

```text
BTC2024    = L failure
XAUEUR2025 = H destination failure
```

A single market-regime veto is not justified.

## 10. Event/FVG research closure

Alternative event/source work was intentionally explored after questioning whether the existing event definition was privileged by its pipeline.

Key corrections:
- event source and downstream pipeline must be evaluated separately;
- body close is better interpreted as interaction state, not automatic direction;
- chart-only direction must exclude spread;
- overlapping FVG zones require unique event IDs.

After those corrections, no FVG or alternative-source module produced a sufficiently robust economic edge. FVG research is closed for now.

## 11. Robustness

13-market-year block Monte Carlo / bootstrap:

```text
combined EV 2.5%  ~ +0.14R
median             ~ +0.30R
97.5%              ~ +0.47R
```

This supports the consumed-panel research freeze but is not external validation.

## 12. Immediate research state

`H = freezeable research module.`

`L1/L2 = frozen controls but individually validation-dependent.`

Do not add more same-panel conditions by default.

Next claim-grade work requires new outcome-blind data and execution validation.
