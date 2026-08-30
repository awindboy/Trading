# V8-001B-r2 — Event-Centered Anchor / Future-Path Dataset Results

Status: `PASS / DATASET REBUILT UNDER V8-001A-r3 COORDINATE`
Date: `2026-08-30`
Production authority: `NONE`
Economic policy/P&L opened: `NO`

## Population

```text
candidate unique timestamps: 66,277
accepted full-history + 240m: 59,438
```

Rejections remain unchanged from r1:

```text
INSUFFICIENT_HISTORY                201
NO_M1_OPEN_AT_T                     212
RIGHT_CENSORED_15M                  674
RIGHT_CENSORED_60M                1,683
RIGHT_CENSORED_240M               4,069
```

The coordinate change did not alter event selection.

## New primary target coordinate

For each accepted anchor:

```text
event_close_reference = source event candle close = 0 origin
future_start_open      = exact M1 open at decision_time
gap_from_event_close   = future_start_open - event_close_reference
```

For 15m / 60m / 240m:

```text
mfe_raw = future max high - event_close_reference
mae_raw = future min low  - event_close_reference
ret_raw = future final close - event_close_reference
```

Auxiliary diagnostic columns retain causal M5 ATR14 normalization:

```text
mfe_atr_aux
mae_atr_aux
ret_atr_aux
```

They are no longer the primary V8 path coordinate.

## Counts by year

```text
2022  12,740
2023  12,862
2024  12,894
2025  12,527
2026   8,415
```

## Performance engineering note

The first r2 labeler used Python slicing for every event/horizon and was too slow for the unified dataset.
The path range calculation was replaced with a Numba interval kernel without changing the population or label
semantics.

Full source load + causal bar build + 59,438 x 3 horizon dataset generation now completes in approximately
31 seconds in the current analysis environment.

This is implementation efficiency only and has no strategy authority.

## Next gate

Train R0/R1/R2/R3 under the frozen event-centered representation protocol.
