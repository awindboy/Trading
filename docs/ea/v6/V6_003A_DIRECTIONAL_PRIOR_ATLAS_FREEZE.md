# V6-003A Directional Prior Atlas Freeze

Status: `FROZEN PRE-OUTCOME MEASUREMENT RECORD`  
Date: `2026-08-29`  
Base GitHub HEAD: `982839b0a1ea166fc534272f2024a72cedfb8326`  
Production authority: `NONE`  
Research panel: GOLD 2022-2025; BTCUSD/XAUEUR/USDJPY 2023-2025  
Untouched reserve: `GOLD 2021`

## 1. Causal observation boundary

For every broad-direct local event:

```text
prior_cutoff = sweep_time
```

Only information from bars whose **bar end is <= sweep_time** may enter a directional prior.

The atomic M1 sweep/recovery bar itself, the later M5 ownership transition that finalizes the local-event direction, and all later information are excluded from the prior calculation.

## 2. Population parity rule

Use the exact committed V3 causal D1 semantics:

```text
calendar D1 resample
-> ATR14 from those D1 bars
-> D1 ATR becomes available at next calendar-day boundary
-> at the event use the latest D1 ATR whose availability time <= trigger time
```

Do **not** impose an extra rule that deletes the first observed D1 bar merely because the raw file begins away from 00:00.

The pre-outcome parity audit produced:

```text
raw direct events       628
causal D1-valid         620
MENV state-valid        540
MENV HIGH_HIGH parents  163
MENV fills              151
exposure accepted       144
```

This exact parity was closed before directional-prior outcomes were interpreted.

## 3. Frozen atlas

### P1 — H1 DMI14 direction

Using the same Wilder implementation already present in `scripts/v6_001b_indicator_atlas.py`:

```text
+1 when +DI14 > -DI14
-1 when +DI14 < -DI14
 0 when equal/unavailable
```

No ADX gate. No magnitude threshold.

### P2 — H1 DISP24 direction

```text
sign(
  last completed H1 close
  -
  completed H1 close 24 H1 bars earlier
)
```

No volatility scaling. No ATR normalization. No magnitude threshold.

### S1 — H1 BOS owner

Exact deterministic H1 pivot/BOS-owner state from the current V3 research code.

### S2 — M30 BOS owner

Exact deterministic M30 pivot/BOS-owner state from the current V3 research code.

### S3 — H1/M30 concordant owner

```text
if H1 owner == M30 owner != 0:
    use that owner
else:
    NEUTRAL
```

S1-S3 are structural controls, not candidate scores.

## 4. Ex-post labels

Only after the independent prior has been frozen may it be compared with the later local-event direction:

```text
ALIGNED
OPPOSED
NEUTRAL
```

The local direction is never used in calculating P1/P2/S1/S2/S3.

## 5. Frozen outcome questions

No strategy authority is implied. For the same local 50% pullback geometry measure:

```text
Fill -> +1R before original structural stop
Fill -> +3R before original structural stop
Fill -> +5R before original structural stop

6h / 24h / 48h
D1-ATR-normalized MFE and MAE
```

Original structural stop wins same-bar target ambiguity.

The pending limit is eligible only from the first M1 bar strictly **after** `trigger_time`, matching the frozen V3 `searchsorted(..., side='right')` semantics.

## 6. Frozen falsification

- P1 must beat or add information beyond P2 to qualify as a conventional directional-pressure edge.
- P2 must be compared with S1/S2/S3 and local-event direction.
- Pooled performance cannot promote.
- Market-year and LONG/SHORT recurrence are mandatory.
- No nearby periods, thresholds, scores, weighted votes or market-specific rescue.
- `OPPOSED` does not imply automatic inversion.
- A result that merely reduces MENV-004 from 144 trades to a small subset is not a successful routing architecture.
