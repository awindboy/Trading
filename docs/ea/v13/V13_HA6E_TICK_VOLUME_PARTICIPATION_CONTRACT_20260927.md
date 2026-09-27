# V13 HA-6E tick-volume participation observation contract

Date: `2026-09-27`
Status: `FROZEN BEFORE OUTCOME MEASUREMENT / OBSERVATION ONLY`
Base GitHub main HEAD checked before work: `40f97352e47c66cd3b952f74532b1b71969e79fd`
Market: `GOLD# ONLY`
Window: `2024-01-01 through 2026-08-28 available history`

## Question

Does broker-feed tick participation add Journey continuation/transition information that is not already represented by completed-H4 HA morphology, ordered H1 path, causal raw swing state, HASTOC, MA context and ATR-normalized price geometry?

This stage does not authorize a volume filter, entry, exit, Child veto, SL, TP, sizing rule or threshold.

## Data-semantics gate

MetaTrader/MQL5 distinguishes bar `tick_volume` from `real_volume`. Current GOLD# exports contain `<TICKVOL>` and `<VOL>`.

Before outcome analysis:

1. confirm `<VOL>` availability rather than assuming real exchange volume;
2. confirm positive `<TICKVOL>`, timestamp uniqueness and H4/M1 aggregation parity;
3. quantify year and H4-slot distribution drift;
4. treat tick volume only as a broker-feed activity/participation proxy, never as centralized gold-market traded quantity.

Current quality audit may inform the normalization design but may not inspect future outcome labels.

## One fixed participation representation

Primary decision-time feature:

```text
same_slot_median20_t = median(tick_volume of the previous 20 completed H4 bars
                              whose H4 start hour equals the current H4 start hour)
relative_tick_volume20_t = tick_volume_t / same_slot_median20_t
log_relative_tick_volume20_t = ln(relative_tick_volume20_t)
```

Only bars strictly earlier than the current completed H4 bar enter the baseline. Pre-2024 history may initialize this normalization. The log transform is monotonic and is recorded only as a symmetric coordinate; it is not a second signal.

Why same-slot normalization:

- H4 tick count has strong intraday/session seasonality;
- absolute tick-count scale drifts over years;
- comparing a 16:00 H4 bar directly with a 00:00 bar would confound participation with session structure.

Why 20:

- fixed before outcome measurement;
- approximately one month of prior observations for each H4 slot;
- consistent with V13's existing trailing-20 scale convention;
- not optimized against P/L or reversal labels.

No `volume > average`, z-score, 1.5x/2x spike, percentile trigger, OBV, MFI, VWAP, delta, VSA pattern or volume-profile level is imported in this first probe.

## Causal timing

At the first executable tick after H4 bar `t` completes, the bar's tick volume is finalized. `relative_tick_volume20_t` therefore uses only the completed current bar and previous same-slot bars. No later tick count is used.

## Predeclared descriptive comparisons

1. Confirm full-window coverage and distribution stability by year, side and H4 slot.
2. Display equal-count quintiles of `relative_tick_volume20` only as descriptive bins. Do not promote quintile edges as thresholds.
3. Compare quintiles on unchanged future labels:
   - next-H4 opposite HA color;
   - opposite HA color within three H4 bars;
   - future-defined peak-already-past;
   - remaining favorable excursion;
   - giveback.
4. Test whether relative participation changes outcomes inside comparable existing state:
   - H4 body/range and ATR-normalized HA Delta;
   - H4 Delta contraction / opposite-wick state;
   - ordered H1 path / ending opposition;
   - HA-5 progress rejection/return;
   - HASTOC state;
   - HA-6B EMA50/EMA20 context;
   - HA-6D ADX/DMI state where overlap permits.
5. Report comparison coverage. Do not claim independence from sparse overlap.
6. Report 2024/2025/2026 × LONG/SHORT direction stability.
7. Audit all `>=10 H4` long Journeys for false participation warnings and remaining favorable excursion.

## Interpretation boundary

A monotonic relation in consumed 2024-2026 data is descriptive only. Tick volume is feed-dependent and can change with liquidity-provider/server quote behavior. Even if it adds information, action research requires a later separately frozen HA-7 contract and future untouched validation.

## Stop conditions

Stop HA-6E without action authority if any of the following holds:

- normalized participation has weak/non-stable outcome separation;
- apparent separation disappears after existing-state overlap controls;
- year/side direction is inconsistent;
- long-Journey false-warning cost is large;
- useful behavior depends on post-hoc thresholds;
- feed/session dependence dominates the result.
