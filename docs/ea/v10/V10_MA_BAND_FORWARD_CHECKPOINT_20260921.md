# V10 MA-band first forward checkpoint

Date: `2026-09-21`
Status: `FORWARD DESCRIPTIVE EVIDENCE / NO THRESHOLD OR TRADE AUTHORITY`
Observed raw-M1 boundary: `2026-09-18 23:57`

## Data and causal compliance

The trusted 2022-01-03 through 2026-08-28 raw-M1 prefix was compared row by row with a new MT5 `GOLD#` extraction. All `1,648,545` timestamps, OHLC values, tick volumes, and spreads matched. The validated source then appended `20,528` new M1 rows through 2026-09-18.

```text
trusted prefix SHA256   626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2
extended M1 SHA256      ebb15194e782c1265fb9eabef2b5324f9909d15b3dd9a70bf2717c5700b61817
MT5 payload fingerprint b2f0ac49995c0afbd27389edd7571a60a15c41e9488dcdddc9ce6d031f0652a7
R7G events SHA256       c4348a34aa35d1e9793283cebbf1a028327c10e3e1c5a4fde2a9e74e3ff801a7
```

The MA ledger was built in one chronological M1 pass. H4/H1/M15 bars and features were emitted only after completion. No threshold, score, or order change was fitted.

## First forward sample

```text
window                 2026-08-31 through 2026-09-18
R7G-selected Children  65
resolved FAST runs     25
Hard SLs               9 (13.85%)
maximum stop streak    5
feature-complete rows  65 / 65
direction / k parity   65 / 65
```

The event CSV records these post-cutoff decisions as `SHADOW_WARMUP`; the frozen R7G weights and entries are still available. Raw M1 supplied the causal state and resolved Child outcomes. Entry parity was exact. Stop differences were at most `0.00446`, consistent with the event CSV's two-decimal formatting.

## Fixed-coordinate result

STOP AUC uses the semantic risk direction frozen before this window. Confidence intervals are FAST-run block bootstrap intervals and are wide because only nine stops exist.

| Coordinate | STOP AUC | Run-block 95% interval |
| --- | ---: | ---: |
| H4 WMA20 OC2 slope / ATR | 0.756 | 0.601–0.955 |
| H4 WMA20 OC2 span / ATR | 0.728 | 0.537–0.955 |
| H1 WMA20 OC2 edge / ATR | 0.685 | 0.510–0.901 |
| M15 SMA60 OC2 deterioration | 0.684 | 0.458–0.904 |
| M15 SMA60 close deterioration | 0.682 | 0.502–0.931 |
| M15 WMA60 OC2 ordering | 0.569 | 0.412–0.787 |

This supports the earlier claim that broad band geometry contains state information. It does not support an actionable threshold. H4 slope/span were stronger than LTF ordering in this short window.

## Structural findings

1. `H1 WMA20 OC2 edge` and `H1 WMA20 OC2 span` are mathematically identical because MA1 equals the current OC2 input. They should be treated as one coordinate, not two independent confirmations.
2. The five-stop streak was not a simple dead-band episode. It included a SHORT k1 followed by LONG k1-k4 on 2026-09-16; several LONG attempts had positive H4 slope and apparently healthy H1/M15 support.
3. Therefore `Parent trend alive` and `current Child safe from immediate stop` remain different questions. A healthy band can coexist with repeated Child stop-outs.

## Decision

- Keep MA bands as continuous Parent/state instrumentation.
- Do not promote breached-line count, ordering, support, slope, span, or a composite threshold.
- Do not claim the first forward window validates stop reduction; no action policy was applied.
- The next mechanistic question is Child-specific stop geometry relative to the H1/M15 band and normal counterflow envelope. Because this question arose after viewing the window, any such coordinate must be frozen first and judged only on chronology after `2026-09-18 23:57`.

Generated row ledgers remain under ignored `output/`. Compact feature and concentration receipts are in `results/ma_band_forward_20260921/`.
