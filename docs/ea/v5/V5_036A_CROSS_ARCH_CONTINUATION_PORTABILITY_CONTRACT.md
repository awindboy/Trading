# V5-036A — Cross-Architecture Continuation-State Portability Contract

Status: `PRE-REGISTERED / ACTIVE NEXT STAGE`
Date: `2026-08-27`
Strategy authority: `NONE`
Production authority: `NONE`

## Motivation

V3 and V5 fail on opposite sides:

```text
V3:
Entry survival weak across markets,
but +1R -> +2R continuation had a strong M30 maturity relationship.

V5 First Cross:
+1R survival is materially better,
but the current WR/payoff architecture cannot reach
WR >=50% + avg positive net >=2R.
```

The scientific question is not to combine rules.

It is:

> Is the V3 M30 continuation relationship a market mechanism that transfers across a completely different Entry family?

## Stage 0 — portability audit before outcomes

Read:
- `docs/ea/D145_RUNNER_GENERALIZATION_RESULTS.md`
- `docs/ea/D146_CONTINUATION_STATE_AUDIT.md`
- exact implementation producing D-145 M30 protected/external identities.

Determine first:

1. Is `one_r_m30_range_progress` a generic causal M30 market state?
2. Or does its meaning depend on V3 Root/FVG scenario ownership and scenario-specific map identities?

If scenario-specific meaning is required:
- do NOT approximate it onto First Cross;
- do NOT run a transfer test;
- classify `NONPORTABLE AS CURRENTLY DEFINED`.

If portable:
- freeze the exact causal definition before reading First Cross continuation through that variable.

## Conditional Stage 1 — transfer falsification

Population:

```text
exact V5-035 clear +1R First Cross development population
GOLD# / BTCUSD# / XAUEUR# / USDJPY#
2023-2025
```

Outcome:

```text
+2R reached before current BE/adverse runner end
vs
exhaust before +2R
```

Inherited prediction:

```text
+2R runners should have LOWER M30 protected->external progress
at +1R than exhaust trades.
```

Report continuous medians and direction by:
- market;
- year;
- LONG/SHORT;
- valid-state coverage.

No threshold may be searched.

## Decision

If nonportable or transfer fails broadly:

```text
close First Cross payoff-rescue research
-> return to payoff-first success-first mechanism discovery
```

If it transfers broadly:

```text
freeze the mechanism result only
-> design a separate preregistered management experiment
-> still require independent validation
```

No transfer result directly authorizes an Entry filter or exit rule.

## Hard stops

- no First Cross partial-fraction tuning;
- no direction veto;
- no slow/EMA score;
- no M30 progress threshold;
- no GOLD# 2021;
- no production EA change.
