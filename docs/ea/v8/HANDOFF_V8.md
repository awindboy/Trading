# V8 Development Handoff

Last updated: `2026-08-31`
GitHub base audited: `0529c204a655e9cc281e1e6f35e5e7883bf4b427`
Current phase: `V8-B2 SOURCE-OF-MOVE CAUSAL DIRECTION / DATA PREFLIGHT`
Production authority: `NONE`
EA authority: `NONE`
Direction authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## Critical correction first

The V8-B1 positive result committed at `0529c204...` is **INVALIDATED_BY_HTF_LOOKAHEAD**.

Do not continue from the stale B1 AUC tables or deploy `config/v8_b1_direction_models.json`.

Read first:

`docs/ea/v8/V8_B1_CAUSAL_ALIGNMENT_INVALIDATION.md`

### Bug

M15/H1 feature bars were selected from a `label=left` resample by bar-start timestamp. For decisions inside the current M15/H1 interval, the model therefore received the later full completed bar, including future prices after the decision.

Leak prevalence over the B1 event table:

```text
M15: 67.78% of event rows
H1:  90.20% of event rows
```

Correct rule:

```text
completed HTF: bar_start + duration <= decision_time
partial HTF: rebuild only from M1 prefix strictly before decision_time
```

## Corrected V8-B1 verdict

Same-family causal re-audit no longer shows a useful stable direction edge.

Completed-only conditional AUC:

```text
15m: 2024 0.666 / 2025 0.553 / 2026 0.534
30m: 2024 0.579 / 2025 0.537 / 2026 0.521
60m: 2024 0.530 / 2025 0.514 / 2026 0.511
```

Causal partial-current HTF also fails to restore the stale result.

Full-population V8-A + corrected V8-B generally fails to improve proper score in 2025/2026 relative to frozen V8-A with a simple side prior.

Therefore:

```text
V8-B1 MT5 direction extension = CANCELLED
V8-B1 coefficients            = DO NOT DEPLOY
```

Permanent regression guard added by this correction pack:

```text
research/ea/v8/v8_causal_time_alignment.py
research/ea/v8/test_v8_causal_time_alignment.py
```

Any future B2 multi-timeframe builder should reuse or match this availability contract rather than recreate bar-start selection ad hoc.

## V8-A status

`FROZEN / UNAFFECTED`

Do not change:

- +/-10.0 price-unit barrier;
- 15m/30m/60m horizons;
- 53-feature causal M1 movement representation;
- walk-forward portable logistic family;
- existing MT5 movement probability semantics.

V8-A does not use the leaky M15/H1 B1 feature path.

Primary artifact remains:

`mt5/indicators/V8MovementProbabilityIndicator.mq5`

## Current V8-B2 question

The failure mechanism is now specific:

> endogenous GOLD history strongly predicts movement intensity but not stable direction once HTF alignment is truly causal.

V8-B2 therefore asks whether source-of-move external context adds sign information:

- USDJPY# as a USD/rate-pressure proxy with caveats;
- XAUEUR# as a cross-gold / USD-translation separator;
- BTCUSD# as a negative-control risk/sentiment market.

Read the frozen contract:

`docs/ea/v8/V8_B2_SOURCE_OF_MOVE_RESEARCH_CONTRACT.md`

## Data access

The current runtime has:

- full GOLD# 2022-2026 M1 raw source.

File-library manifests establish prior raw lineage for:

- USDJPY# 2023-2025;
- XAUEUR# 2023-2025;
- BTCUSD# 2023-2025;
- later USDJPY#/BTCUSD# 2026 YTD working evidence.

But the raw external M1 bytes are not mounted in the active runtime now. Derived result files are not sufficient for causal event-time feature construction.

Therefore the immediate B2 execution gate is:

1. obtain/mount the exact external raw M1 files;
2. hash/data-quality audit;
3. freeze source-age/missing-data rule outcome-blind;
4. run the already-frozen B2 feature/evaluation contract;
5. no rescue if the future-hidden result fails.

## GOLD# 2021

Still untouched. Do not open.

## Reading order next session

1. `docs/ea/v8/AGENTS_V8.md`
2. `docs/ea/v8/HANDOFF_V8.md`
3. `docs/ea/v8/V8_B1_CAUSAL_ALIGNMENT_INVALIDATION.md`
4. `docs/ea/v8/V8_B2_SOURCE_OF_MOVE_RESEARCH_CONTRACT.md`
5. `docs/ea/v8/V8_005_MOVEMENT_PROBABILITY_INDICATOR.md`
6. `docs/ea/v8/DECISIONS_V8.md`
7. `docs/ea/v8/RESEARCH_STATE_V8.md`
8. `docs/ea/v8/V8_RESEARCH_JOURNEY.md`

Refresh GitHub HEAD before further work.
