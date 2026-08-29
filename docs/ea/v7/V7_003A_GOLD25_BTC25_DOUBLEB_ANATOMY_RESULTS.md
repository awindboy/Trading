# V7-003A GOLD25 / BTC25 Double-B Anatomy Results — Working Result 1

Status: `DISCOVERY / OUTCOME OPENED / PARTIAL — V7-003A CONTINUES`
Date: `2026-08-30`
GitHub base inspected: `06b59aae7a9cf881e33ef0a7a359a02b29290335`
Validation authority: `NONE`
Production authority: `NONE`

## 1. Scope and hard boundary

This result follows `AGENTS_V7.md`, `HANDOFF_V7.md`, and `V7_003A_GOLD25_BTC25_DEVELOPMENT_PLAN.md`.

Frozen development cohort only:
- `GOLD# 2025`
- `BTCUSD# 2025`

`USDJPY#`, `XAUEUR#`, other years and other markets were deliberately not opened for subgroup-performance selection.
No SL/TP, R, entry, staging, or P/L optimization was performed.

Outcome has now been opened for GOLD25/BTC25. Both are permanently consumed discovery data and cannot be used for V7-004 validation.

## 2. Raw data audit

### Inputs actually used

| File | Role | Rows | Coverage | SHA256 |
|---|---|---:|---|---|
| `GOLD#_M1_202401020100_202412302358.csv` | GOLD indicator warm-up only | 353,837 | 2024-01-02 01:00 — 2024-12-30 23:58 | `21518cf93f059b0f44743419320cfd1aa0939b1de7dd8f7cccf0b581a6785160` |
| `GOLD#_M1_202501020800_202512302358.csv` | GOLD25 cohort | 351,929 | 2025-01-02 08:00 — 2025-12-30 23:58 | `d8d5f2ecc6e6fb6882209a4bf21e5cd37fbe6e50eea7e09421b0cd7a8b3e7605` |
| `BTCUSD#_M1_202301010000_202512310000.csv` | BTC warm-up + BTC25 cohort | 1,571,009 | 2023-01-01 00:00 — 2025-12-31 00:00 | `d477f7063da7e91e959dc4126a4d49b7e8665316012428cb822ab6e97133c9fe` |

Checks on all three used files:
- duplicate timestamps: `0`
- non-monotonic timestamps: `0`
- OHLC consistency violations: `0`
- negative spread/price anomalies: `0`

2025 spread fields are populated, but the raw integer `SPREAD` values are symbol-point units. They are not compared cross-market as economic cost without symbol point/tick-value metadata.

### H1 derivation

Convention: raw server timestamp floored to the hour; open=first M1 open, high=max, low=min, close=last M1 close.

- GOLD25: 5,875 H1 bars; 95.51% contain all 60 M1 rows; minimum 25 M1 rows in an H1 bar.
- BTC25: 8,737 H1 bars; 99.36% contain all 60 M1 rows; minimum 1 M1 row in an H1 bar.

Partial bars are retained and flagged by `M1_COUNT`; no event was silently deleted because of sparse minutes.

### Server time status

The CSV itself carries no timezone metadata. GOLD weekly open/close shifts around DST are consistent with an EET/EEST-style broker server clock (UTC+2 winter / UTC+3 summer), but this is an inference, not frozen authority.

Exact Asia/Europe/US first-H1 mapping is not yet authoritative. Therefore this result does **not** invent session labels or KTR values. In the anatomy ledger:
- `session = UNKNOWN_SESSION_BOUNDARY_NOT_FROZEN`
- `KTR = blank`
- `KTR_status = NOT_COMPUTED_UNTIL_SESSION_OPEN_H1_MAPPING_IS_FROZEN`

This is an intentional fail-closed choice under V7-D009.

## 3. Double-B detector audit and frozen census

Frozen detector:
- H1
- Band A: SMA20, 2 population standard deviations, applied to CLOSE
- Band B: SMA4, 4 population standard deviations, applied to OPEN
- UPPER: event H1 high reaches/exceeds both upper bands
- LOWER: event H1 low reaches/exceeds both lower bands
- BOTH retained
- indicator values include the closed event bar, matching a decision made after H1 close

Warm-up correction: GOLD 2024 was loaded before computing 2025 bands. Computing from the 2025 file alone would make the first 20 H1 values artificially unavailable and was rejected.

### Census

| Market | H1 bars | UPPER | LOWER | BOTH | Total DB | DB rate |
|---|---:|---:|---:|---:|---:|---:|
| GOLD# 2025 | 5,875 | 227 | 194 | 3 | 424 | 7.22% |
| BTCUSD# 2025 | 8,737 | 311 | 324 | 4 | 639 | 7.31% |
| **Total** | 14,612 | 538 | 518 | 7 | **1,063** | 7.28% |

The complete census was frozen **before** future-path analysis:
- file: `ledgers/v7/V7_003A_GOLD25_BTC25_DOUBLEB_CENSUS_FROZEN.csv`
- SHA256: `7fb5224fb27c16454f760847f4bd4a5d59045beb2c79ad554635eff6a8be7251`

Important correction to intuition: the formal detector produces roughly one DB H1 in fourteen H1 bars, not a few dozen events per year. The V7-002 24-event set was a selected pilot, not a census. This does not invalidate the method definition, but “rare event” must not be mentally equated with “extremely sparse sample.”

## 4. Outcome-anatomy convention

Future was opened only after census freeze.

For 1/4/12/24 horizons, the ledger records next available H1-bar path:
- high-side excursion from event close;
- low-side excursion from event close;
- path span;
- end-close displacement.

For cross-market descriptive comparison only, a causal auxiliary scale `PRE_ATR20` is used: mean True Range of the 20 H1 bars preceding the event, excluding the event H1.

`PRE_ATR20` is **not KTR**, has no strategy authority, and is not substituted into SL/TP logic.

`same-side excursion` means movement toward the DB side (UPPER->up, LOWER->down). It is anatomy vocabulary, not trade direction.

## 5. Finding A — Double-B side is not direction authority

At 24 future H1 bars:

| Market | N (non-BOTH, resolved) | same-side excursion > opposite excursion | 95% Wilson CI |
|---|---:|---:|---:|
| GOLD# | 419 | 52.03% | 47.25%–56.77% |
| BTCUSD# | 633 | 46.92% | 43.06%–50.81% |

This is close to non-directional at aggregate level.

GOLD reveals why aggregate labels can mislead:
- UPPER DB: same-side dominance = `60.62%`
- LOWER DB: same-side dominance = `41.97%`
- 24H future close was above event close after `65.49%` of UPPER events and `64.25%` of LOWER events.

Thus 2025 GOLD context was strongly upward-biased: UPPER events often continued up, while LOWER events often reversed up. Treating DB side as LONG/SHORT would erase the dominant context.

BTC was much more symmetric:
- UPPER same-side dominance `46.93%`
- LOWER same-side dominance `46.91%`

**Status:** strongly supports V7-D003: `DOUBLE-B != DIRECTION`.

## 6. Finding B — outside-both close is neither sufficient nor necessary

24H same-side dominance when the event close finished outside both relevant bands:
- GOLD: `53.37%` (208 events)
- BTC: `50.71%` (282 events)

Strong contradiction cases remain common. Define only for descriptive audit `|polarity| > 0.5`, where polarity=(same excursion-opposite excursion)/(same+opposite):
- close outside both, but strong opposite-side future: GOLD `25.00%`, BTC `28.72%`
- did not close outside both, but strong same-side future: GOLD `28.91%`, BTC `25.93%`

A dramatic close is therefore evidence about the event, but not a reliable continuation classifier by itself.

**Status:** independently reproduces V7-D006 on the new development cohort.

## 7. Finding C — DB does select high post-event movement, but much is volatility selection

Median future path span / prior ATR20:

| Market | Horizon | Non-DB | DB | DB - non-DB median | bootstrap 95% CI of median difference |
|---|---:|---:|---:|---:|---:|
| GOLD | 4H | 1.82 | 2.33 | +0.51 | +0.44 to +0.61 |
| GOLD | 12H | 3.43 | 3.99 | +0.56 | +0.37 to +0.81 |
| GOLD | 24H | 5.15 | 5.79 | +0.64 | +0.38 to +0.89 |
| BTC | 4H | 1.76 | 2.52 | +0.76 | +0.64 to +0.92 |
| BTC | 12H | 3.33 | 4.12 | +0.79 | +0.56 to +1.04 |
| BTC | 24H | 4.99 | 6.23 | +1.25 | +0.92 to +1.54 |

So DB events are followed by larger path ranges than ordinary H1 bars.

However, after stratifying bars by the **event candle's own TR / prior ATR** decile, the DB advantage is not monotonic and is often small inside a volatility stratum. Example 12H span medians:
- GOLD TR decile 7: DB 3.41 vs non-DB 3.66
- GOLD decile 10: DB 4.26 vs non-DB 3.72
- BTC decile 8: DB 3.55 vs non-DB 3.66
- BTC decile 10: DB 4.63 vs non-DB 4.24

Interpretation: DB is at least partly a detector of already-high-volatility candles and subsequent volatility clustering. It is **not yet established** that the two-band condition adds independent forward-volatility information beyond event-candle magnitude/context.

## 8. Finding D — “mature move = terminal” is too naive

A signed pre-move variable was defined without outcomes:
- positive = preceding 24H displacement was already toward the DB side;
- negative = preceding displacement was against the DB side;
- normalized by prior ATR20.

Top quartile of same-side pre-move did **not** show a universal reversal/terminal pattern:
- GOLD top pre-move quartile: 24H same-side dominance `56.19%`
- BTC top pre-move quartile: `50.94%`

So simple extension/maturity alone does not separate fresh from terminal expansion.

Event-candle shock size is also market-dependent:
- GOLD top quartile TR/prior-ATR: 24H same-side dominance `39.05%`, median polarity `-0.156`
- BTC top quartile TR/prior-ATR: `50.94%`, median polarity `+0.088`

For GOLD, the largest DB event candles more often became opposite-side dominant; BTC did not reproduce that relation.

A 2x2 descriptive split further shows interaction:
- high event TR + **low** same-side pre-move: same-side dominance GOLD `41.49%`, BTC `39.66%`
- high event TR + **high** same-side pre-move: GOLD `52.99%`, BTC `52.48%`

This suggests “terminal” may depend on the relationship between shock size and pre-existing move, not either variable alone. It remains discovery only; no threshold is promoted.

## 9. Finding E — many DB events become genuinely two-sided

Within the next 24 H1 bars, both DB-side and opposite-side excursion reached at least 1 prior ATR after:
- GOLD: `55.61%`
- BTC: `58.14%`

Both sides reached at least 2 prior ATR after:
- GOLD: `21.72%`
- BTC: `26.07%`

This is not a P/L result. It shows that a large fraction of DB events evolve through meaningful two-sided path geometry. A single immediate direction at event close is structurally difficult in many cases, supporting the need for `WAIT_CONFIRM` and explicit two-stage/reclaim logic.

## 10. Finding F — single scalar context variables are weak

Spearman relationship with 24H DB-side polarity is small for the tested causal descriptors.

BTC: all tested absolute rho values were below ~0.09, including event TR, 24H pre-move, MA extension/slope, Bollinger width changes, close location, body/range, and recent DB count.

GOLD: the largest side-adjusted interpretable correlations were still weak; e.g. event TR rho `-0.082`, side-adjusted close location rho `+0.089`, signed 24H pre-move rho `+0.074`.

This argues against immediately building a mechanical additive score from these variables. The useful information, if present, is more likely interaction/context/state-dependent.

## 11. Self-corrections made during this run

1. **Warm-up correction:** GOLD 2024 was added before 2025 indicator calculation so early-2025 BB values use prior history.
2. **Detector skepticism:** the unexpectedly large event count triggered a re-audit. Population-vs-sample standard deviation, current-vs-previous-band alignment, close-vs-touch semantics, and repeated events were checked. The frozen document semantics support the current-bar touch detector; events were not deduplicated.
3. **Excursion correction:** an early implementation allowed a future high below event close to produce a negative 'up excursion'. Excursions were corrected to be non-negative; path span is stored separately. Census was unaffected because future had not been opened when census was frozen.
4. **KTR fail-closed:** exact session first-H1 mapping was not inferred into authority. KTR/session columns remain explicitly unknown rather than using an invented proxy.

## 12. What is supported vs not supported

### Supported as discovery evidence
- DB side alone has essentially no direction authority.
- outside-both close alone is not a classifier.
- DB events identify unusually active/volatile states, though independence from candle size is not established.
- simple move maturity is insufficient to identify terminal expansion.
- GOLD and BTC can show opposite relationships for the same anatomy variable.
- two-sided and multi-stage post-event paths are common enough that WAIT/confirmation must remain first-class.

### Not supported / not yet done
- no V7 profitability claim;
- no archetype classifier;
- no fixed threshold on TR, body, MA distance, or Bollinger width;
- no KTR conclusion;
- no session-opening break conclusion;
- no S/R conclusion;
- no SL/TP/entry/staging result;
- no validation result.

## 13. Next V7-003A work

Remain in V7-003A.

Priority order:
1. freeze exact broker-server session-opening H1 mapping for Asia/Europe/US from method/environment authority;
2. fill session and KTR fields without changing the frozen event census;
3. add causal S/R and session-opening high/low relationships;
4. inspect event clusters that contradict simple rules: large-shock reversal, strong-looking outside close that fails, non-outside continuation, two-sided expansion;
5. only then compress recurring path families into a context atlas candidate for V7-003B.

Do not move to KTR multiplier, entry, or staging optimization from this result.
