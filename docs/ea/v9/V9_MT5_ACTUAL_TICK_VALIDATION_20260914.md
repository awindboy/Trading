# V9 MT5 Actual-Tick Validation

Date: `2026-09-14`
Status: `ACTUAL-TICK VALIDATION EVIDENCE / CURRENT EXECUTION EVIDENCE`

## Inputs

```text
V9_R0_events.csv
SHA256 c6e4a1117c1c0b8b073b09caaa433d940eae858dea1d9f9bc8c63fc95ab1c37c

V9_R0_trades.csv
SHA256 bb4167b9c53ba3c73320f7dc032acc83f9d97bc6898aa04818947e167dc16bce
```

Tester initialization was logged at `2021-12-31 18:50:59`; strategy-period ticks began in 2022 and the last logged tick was `2026-09-11 23:57:59`.

## Reference-period result

For entries through `2026-08-28`, matching the supplied M1 research horizon:

```text
closed Children  1,316
wins                792
losses              524
WR                 60.18%
PnL             +5,028.62
PF                  1.425
```

## Full uploaded closed ledger

```text
closed Children  1,322
wins                795
losses              527
WR                 60.14%
PnL             +4,954.61
PF                  1.412
avg winner          +21.34
avg loser           -22.79
```

Two positions remained open at tester deinitialization and are not included in closed-trade PnL.

## Geometry and Arrival parity

The M1 full-era reference contains `1,733` Arrival minutes.

Actual tick replay through `2026-08-28` logged `1,839` H4-liquidity Arrival events across `1,734` minutes. Of those minutes:

- all `1,733` reference Arrival minutes were present;
- reference side mismatch: `0`;
- reference collapsed extreme-price mismatch: `0`;
- one extra minute was genuine tick-level two-sided/overlap activity;
- `87` minutes contained more than one H4-liquidity raid;
- maximum raids inside one minute: `5`.

Therefore the object geometry largely matched; the major semantic difference is real intraminute sequencing that M1 aggregation cannot represent.

## Role results

```text
ANCHOR_CHILD
355 trades / WR 37.2% / +2,439.43 / PF 1.498
median hold ~60.93h

CONTINUATION_CHILD
967 trades / WR 68.6% / +2,515.18 / PF 1.353
median hold ~6.64h
```

## Direction results

```text
UP    731 / +4,836.20 / PF 1.832
DOWN  591 /   +118.41 / PF 1.019
```

SHORT is near breakeven under actual ticks. This is a diagnostic weakness, not current permission to ban SHORT.

## Exit results

```text
CHALLENGE_OPENS                   232 / +5,529.48 / PF 4.064
NEXT_H4_LIQ                      761 / +7,901.62 / PF 5.563
STRUCTURAL_SL                    255 / -6,324.70
TICK_COLLISION_STOP_CHALLENGE     30 /   -978.86
TICK_COLLISION_STOP_NEXT_H4_LIQ   44 / -1,172.93
```

Tick collision evidence confirms that the old M1 ambiguous bucket was not economically neutral.

## Structural distance

Actual entry-to-structural-SL distance:

```text
mean   31.86 GOLD
median 22.56
P75    36.97
P90    65.44
P95    91.72
P99   164.19
max   225.65
```

Wide absolute stops remained viable after ERA normalization. Do not reintroduce a fixed-GOLD stop limit.

## Session / weekday / duration

Derived tables are stored under `results/prototype_20260914/`.

All weekdays and all four broad source-time session buckets were gross-positive. This is descriptive only. The source timestamp was not remapped to London/New York DST sessions, so do not label these buckets as named global sessions without a separate timezone contract.

Holding-time cohorts show a strong surviving-Anchor right tail after 3+ days, while 4h-3d cohorts were negative. This contains survivorship effects and is not a duration-filter authority.

## Broker/session failures

```text
ENTRY_FAIL   10  -> ret=10018 market closed
CLOSE_FAIL   16  -> ret=10018 market closed
retry closes 16
```

Session-close/reopen gap risk is therefore part of the real execution problem and must remain logged in forward demo.

## Post-reference forward-like sample

Entries after `2026-08-28` in this tester run:

```text
6 closed
3 wins / 3 losses
PnL -74.01
PF 0.582
```

Two additional positions were still open at tester end. This sample is too small to treat as independent validation.
