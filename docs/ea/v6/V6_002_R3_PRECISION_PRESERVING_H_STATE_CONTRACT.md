# V6-002 R3 — Precision-Preserving H-State Contract

Status: `ACTIVE CHILD / PRE-OUTCOME CONTRACT`  
Date: `2026-08-28`  
Primary development market: `GOLD# 2023-2025`  
Production authority: `NONE`

## 1. Research question

> Can V6 preserve the frozen V3 local precision substrate while using H4 maturity only to determine when the H large-payoff destination remains healthy?

This child exists because V6 R2 improved GOLD period robustness but destroyed V3 economics on some independent markets, especially BTCUSD. The suspected error was replacing local precision too broadly rather than using state inside the relevant strategy stage.

## 2. Hypothesis source

The H maturity hypothesis is not a fresh indicator search inside Candidate B. It comes from three already-consumed observations:

1. broad-event R1/R2 work found H healthier in `H4 ADX14 <25` than `>=25`;
2. pre-existing V3 H `BOTH` evidence showed no +5R winners in the more progressed state;
3. pre-existing D-145 continuation evidence associated large continuation with less-consumed M30 structure.

These sources motivate one fixed H-stage hypothesis. They do not authorize threshold alternatives.

## 3. Frozen shadow population

Use the exact V3 Candidate-B Module-H direct population before exposure on GOLD 2023-2025.

Expected development parity:

```text
44 H-direct fills
14 TP5
27 SL
3 BE
```

No Candidate-A gate, direct-transfer rule, pullback geometry, SL, payoff, direction rule, or L rule may change during the shadow audit.

## 4. Fixed state

Attach completed H4 Wilder ADX(14) at the H parent trigger time.

```text
NOT_MATURE = ADX14 < 25
MATURE     = ADX14 >= 25
```

No alternative threshold, period or timeframe is allowed inside R3.

## 5. Primary shadow evaluation

Use the frozen Candidate-B H payoff representation:

```text
+3R realize 25%
residual -> BE
final -> +5R

TP5 = +4.5R
BE  = +0.75R
SL  = -1R
```

Report for NOT_MATURE and MATURE:

```text
N
positive rate
avg positive R
EV/trade
total R
max DD / loss streak in chronological subset
year split
direction split
winner concentration
```

AUC is not used.

## 6. Frozen criterion for constructing one downstream R3 strategy variant

Only if NOT_MATURE H has all of:

```text
pooled EV > 0
2023 EV > 0
2024 EV > 0
2025 EV > 0
pooled LONG EV > 0
pooled SHORT EV > 0
```

and MATURE H is economically weaker than NOT_MATURE H in pooled EV, one downstream R3 strategy variant may be constructed.

MATURE H does not need to be negative in every cell. The hypothesis is that less-mature H is a robust healthy specialist and mature H is materially weaker.

If the criterion fails:

```text
R3 H-maturity formulation CLOSED
no 2022 use for R3
no ADX threshold rescue
```

## 7. Downstream R3 strategy, only if shadow criterion passes

The one allowed R3 strategy variant is:

```text
exact frozen V3 Candidate-B common substrate
H unchanged except MATURE H is suppressed before fill authorization
primary frozen V3 L unchanged
frozen opposite-direction exposure rule unchanged
```

This is deliberately precision-preserving. It is not the broad R2 router.

No new H payoff management is allowed in the first R3 variant.

## 8. Development comparison

Compare on GOLD 2023-2025:

```text
V3 Candidate B
R2 benchmark
R2P alternate
R3 candidate
```

Report the complete economic/risk vector. Do not judge R3 from WR alone.

## 9. Historical/cross-market sequence

Only after R3 is fully frozen from GOLD 2023-2025:

1. apply unchanged R3 to consumed GOLD 2022 as historical stress comparison;
2. apply unchanged R3 to XAUEUR/USDJPY/BTCUSD 2023-2025 architecture-diagnostic panel;
3. do not tune thresholds/payoff/market selection from those outcomes.

These environments cannot promote R3 as pristine validation; they can falsify or diagnose portability.

## 10. Opposite thesis

> The apparent ADX maturity relation is only a broad-GOLD artifact. Once V3 local precision is preserved, ADX adds no useful H-stage information, or it damages H frequency/EV without meaningful robustness gain.

## 11. Simpler alternative

> V3 H direct-transfer precision alone explains the healthy H subset; no extra H4 state is needed.

The R3 audit must compare against the full frozen H-direct control, not only report the selected subset.

## 12. Kill/degrade conditions

Close or downgrade R3 if:

- NOT_MATURE H has non-positive EV in any development year;
- LONG or SHORT pooled EV is non-positive;
- mature/not-mature difference is economically negligible;
- R3 strategy improves one headline metric only by destroying average winner or EV;
- cross-market diagnostic shows systematic destruction without any plausible market-suitability distinction.

Do not change ADX definition to rescue the child.

## 13. 2021

GOLD 2021 remains untouched regardless of R3 outcome until a later explicit freeze assigns its role.
