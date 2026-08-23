# D-154O Stage A Results and Stage-B Freeze

Status: `STAGE A COMPLETE / STAGE B COHORT FROZEN BEFORE NEW 2025 OUTCOMES`  
Date: `2026-08-24`  
Base Git HEAD: `0b317facba97f4edc305d0d4c82fbe5bd10a9739`  
Environment: `XM Ultra Low`

## Stage-A disposition

The 32-symbol outcome-blind screen is accepted.

Nominal frozen week:

```text
2026-08-17 00:00 .. 2026-08-23 23:59:59
broker/server time
```

The eight crypto symbols were exported through approximately `2026-08-23 19:44`,
leaving a ~4h15m tail truncation (~2.5% of the calendar week). This is retained as
a data-quality note rather than silently hidden.

Sensitivity checks performed before Stage-B outcomes:
- removing Sunday entirely did not change the common top-8 shortlist set;
- removing crypto weekend data did not move BTCUSD# out of the shortlist.

Disposition:

```text
ACCEPTED_WITH_MINOR_CRYPTO_TAIL_TRUNCATION
NO RERUN REQUIRED
```

## Selection rule frozen before new 2025 outcomes

No weighted GoldLikeScore is used.

```text
quality_status = OK
AND
raw spread / M1 TR <= 0.714286
AND
spread / generic M1 FVG <= 2.000000
```

The boundary is the common top-8 block ending at `USDJPY#`. The next raw
spread/M1-TR observation is `GBPUSD# = 1.000000`.

## Frozen Stage-B cohort

| Symbol | Cohort | raw spread/M1 TR | spread/generic M1 FVG | spread bps |
| --- | --- | ---: | ---: | ---: |
| GOLD# | REFERENCE | 0.159509 | 0.440678 | 0.594866 |
| XAUJPY# | GOLD_LIKE | 0.291829 | 0.893487 | 1.068626 |
| XAUCNH# | GOLD_LIKE | 0.410959 | 1.212938 | 1.515458 |
| BTCUSD# | GOLD_LIKE | 0.429799 | 1.209677 | 2.151591 |
| XAUEUR# | GOLD_LIKE | 0.432836 | 1.252660 | 1.503478 |
| GAUCNH# | GOLD_LIKE | 0.571429 | 1.620192 | 2.044446 |
| GAUUSD# | GOLD_LIKE | 0.622642 | 1.736842 | 2.331612 |
| USDJPY# | GOLD_LIKE | 0.714286 | 2.000000 | 0.631353 |
| GBPUSD# | CONTROL | 1.000000 | 2.600000 | 0.813549 |
| SILVER# | CONTROL | 1.021739 | 2.764706 | 7.144377 |
| EURUSD# | CONTROL | 1.111111 | 2.500000 | 0.862314 |
| ETHUSD# | CONTROL | 1.151515 | 4.042553 | 8.382341 |

Reference:

```text
GOLD#
```

Gold-like candidates:

```text
XAUJPY#
XAUCNH#
BTCUSD#
XAUEUR#
GAUCNH#
GAUUSD#
USDJPY#
```

Negative controls:

```text
GBPUSD#
SILVER#
EURUSD#
ETHUSD#
```

## Independence caveat

These are correlated GOLD-family replications, not independent market confirmations:

```text
GOLD#
XAUJPY#
XAUCNH#
XAUEUR#
GAUCNH#
GAUUSD#
```

The most decision-useful independent low-friction confirmation is therefore
`USDJPY#`; `BTCUSD#` is also low-friction but already has prior D154UL 2025 evidence.

Boundary comparison of special interest:

```text
USDJPY#  vs  GBPUSD# / EURUSD#
```

Asset-class controls:

```text
GOLD family vs SILVER#
BTCUSD#   vs ETHUSD#
```

## Stage-B contract

Run exactly the frozen 12-symbol cohort:

```text
XM Ultra Low
2025-01-01 .. 2025-12-31
Every tick based on real ticks
V3E mode 9
EM OFF
D151 ON
D154K ON
D154M ON
```

Primary evidence:
- Fill count and right censoring;
- Fill -> +1R actual survival;
- LONG/SHORT survival;
- exact D154K spread/reactionTR, spread/1R, spread/selected-FVG;
- risk/reactionTR and FVG/reactionTR;
- D154M shadow survival and actual-SL -> shadow-+1R flips.

Do not add/drop markets after any new Stage-B outcome is known.

No Entry gate, per-trade spread threshold, symbol veto, SL/TP/sizing/SP/EM change
is authorized by the Stage-A screen.
