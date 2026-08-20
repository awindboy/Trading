# D-145 Runner Market-Context Audit

Date: 2026-08-21
Build: `1.92R1L7`
Phase: `RUNNER_MARKET_CONTEXT_AUDIT_V1_LIGHTWEIGHT`
Strategy authority: **NONE**

## Research question

Do not optimize a take-profit R from aggregate hit rates. The question is:

> Given the same valid actual Fill, why does one market state produce only a ~1R reaction while another produces 2R or more directional delivery?

The comparison population is deliberately conditional:

```text
all actual fills
  -> first separate <1R failures from +1R successes
  -> within +1R successes compare SL-before-2R vs 2R+ runners
```

This removes entry success as the main confound when studying continuation length.

## Snapshot A — Actual Fill

At exact Fill observation, record only causally-known information:

- current H1/M30 map owners, owner age, latest BOS age and PB history;
- current protected-to-external range position and remaining external room measured in the actual Fill-to-SL R unit;
- current latest-12 M30 wave progression, net directional advance normalized by mean leg size, PB count, and recent/prior leg expansion;
- current M1 trend/protected/external state;
- Root/FVG geometry and causal-stage elapsed times;
- selected-FVG to Fill maximum favorable displacement and adverse retrace gathered prospectively from ticks;
- frozen structural objective room in actual R.

## Snapshot B — First +1R

When the exact exit-side price first reaches +1R before SL, record:

- time from Fill to +1R;
- max adverse R before +1R;
- current H1/M30/M1 market state again;
- new same-direction and opposite-direction structure events since Fill;
- new same-direction and opposite protected breaks since Fill.

## Exact labels

For each actual Fill, exact ticks resolve independently:

```text
1R before SL
2R before SL
3R before SL
structural TP before SL
```

LONG uses Bid and SHORT uses Ask for outcome price. Unresolved targets at tester end are right-censored; they are not synthesized from OHLC.

## Runtime constraint

D-144 tracked thousands of stage/mirror barriers and made GOLD roughly 9x slower. D-145 removes that fan-out. Only selected-FVG pre-fill trackers and actual-filled runner trackers are tick-active.

## Governance

The following are explicitly prohibited from this audit:

- choosing a fixed TP because one pooled R point crosses 50%;
- age/time/range/progression/displacement cutoff mining;
- using outcome-known information in the Fill snapshot;
- promoting a GOLD-only relationship;
- consuming 2021.

A useful mechanism should preserve the **direction of the relationship** across LONG/SHORT, calendar blocks, additional symbols, and later untouched evidence even if the numerical values differ.
