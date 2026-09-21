# V10 compact research state

Date: `2026-09-21`
Authority: `RESEARCH ONLY`
Production authority: `NONE`
Consumed cutoff: `2026-08-28 23:57 raw M1`
Final reserve: `GOLD# 2021 SEALED`

## 1. Core architecture

```text
H4 FAST HA
-> campaign/run segmentation
-> participation opportunities
-> first opposite completed FAST HA exit comparator

Child
-> independent Hard SL
-> never resurrected after stop

R4/R5/R7G
-> frozen historical participation/sizing comparator

normalized state
-> shadow evidence only
```

## 2. Data and causality

- Official raw M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`.
- Higher timeframes are reconstructed chronologically from raw M1.
- R3 universe SHA256: `f352a99c746752ca259da33dbdaee9d8f0cb874bd01cf520a487fe1bdbf82609`.
- Historical universe: 6,770 opportunities, 2,139 resolved FAST runs.
- The matched R7G economic slice used in the 2026-09-21 studies contains 1,649 resolved intended Children.

## 3. Frozen historical comparator

R7G semantics:

```text
R4 weight == 1
AND R5 EV > 0
AND mean realized R of eligible prior-exited Children
    over the latest 180 completed H4 indices > 0
-> upgrade 1 unit to 3 units
else preserve R4 action
```

Consumed M1-verified comparison:

| Policy | Structural R | PF_R | DD_R | Raw price-PnL | Spread-adjusted price-PnL |
| --- | ---: | ---: | ---: | ---: | ---: |
| R4 | +485.07 | 1.583 | 50.32 | +23,234.65 | +22,590.76 |
| R7G | +741.01 | 1.682 | 59.71 | +30,883.72 | +30,074.67 |

This does not establish live expectancy. R7G is right-tail dependent and uses a post-selected sizing overlay.

## 4. Retained shadow hypotheses

### K1 extreme STOP

Purpose-specific Robust Logistic q97.5 remains a historical/future-shadow research object only. It is not integrated as trade authority. The full 2022-2026 history is consumed.

### Intrabar seed defense

Frozen observational rule:

```text
newest live R7G 1-unit Child
+ forming H4 +60m
+ normalized provisional FAST-HA margin <= -0.1641973584634039
-> log hypothetical newest-Child exit only
```

Historical diagnostic: 24 actions, 8 Hard SLs prevented, `+4.69R`, maximum stop streak unchanged.

### Normalized MA state

Retained continuous coordinates:

- H4 WMA20 OC2 slope/span divided by H4 ATR180;
- H1 WMA20 OC2 edge/span divided by H1 ATR180;
- M15 SMA/WMA60 support, ordering, and deterioration as line fractions.

H1 WMA20 OC2 edge/span STOP AUC remained about `0.706 / 0.737 / 0.752` in 2024/2025/2026. Stable discrimination did not produce a stable action rule.

## 5. Closed findings

| Branch | Decision | Reason |
| --- | --- | --- |
| broad regime admission | closed | unstable and removed too much right tail |
| generic negative-R head | closed | target did not yield durable action value |
| direct next-HA prediction | closed as authority | predictability mostly restated forming HA math |
| broad intrabar NHA exit | closed | reduced stops but lost R; streak not improved |
| Ridge action-value exit | closed | pooled `-57.10R` |
| progression proof | closed | `-250.99R` |
| damage-repair lockout | closed | `-320.42R` |
| combined lockout | closed | `-509.22R` |
| fixed MA breached-line rule | closed | meaning changed by MA family/horizon; non-monotonic |
| post-hoc no-k3p-SHORT | closed | diagnostic only |

## 6. Liquidity-era evidence

Median H4 ATR180 changed materially:

```text
2022   9.66   (0.555% of price)
2023   8.92   (0.469%)
2024  12.63   (0.500%)
2025  19.85   (0.582%)
2026  45.48   (1.065%)
```

Therefore raw point/dollar thresholds are not portable. Use same-timeframe ATR normalization and scale-free band fractions.

## 7. EA state

- `V10R7G_ExactActualTickReplayEA.mq5`: frozen historical execution reference.
- `V10R7G_FullEmbeddedML_EA.mq5`: chart-native embedded research EA.
- User MT5 execution exists; market-closed order failures are known and intentionally deferred.
- One historical generic-export R5 EV-sign mismatch remains documented (`925/926` versus native `926/926`).
- No live or production authority.

## 8. Active next contract

`V10_NEXT_RESEARCH_CONTRACT_NORMALIZED_STATE_FORWARD_20260921.md`

The next valid evidence is future-only shadow logging. No further consumed-data parameter search is authorized.
