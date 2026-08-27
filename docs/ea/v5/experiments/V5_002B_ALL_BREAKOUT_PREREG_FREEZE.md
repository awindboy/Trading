# V5-002B — All-Breakout Population Redesign Freeze

Status: `PRE-REGISTERED BEFORE Q1/Q2/Q3 OUTCOME ANALYSIS`
Freeze time: `2026-08-27T06:02:51Z`
Parent: `V5-002 original episode-de-dup design`
Reason for redesign: `CONFOUNDED / DESIGN INSUFFICIENT at outcome-blind population census`

## Census failure that triggered redesign

The original frozen-range re-arm rule produced severe path-dependent sampling:
- 26,684 retained events total;
- 60m: DOWN 11,383 vs UP 671;
- BTCUSD# 60m: DOWN 4,148 vs UP 10;
- USDJPY# retained zero 2025 events;
- several UP series stopped generating events in 2023 because one old frozen range remained active for years.

No Q1/Q2/Q3 directional outcome relationships were inspected before this redesign.

## New population

For each symbol and each pre-registered scale:

```text
60m / 240m / 1440m
```

at every M1 bar `t`:

```text
high_W = max(high) over observed bars [t-W,t)
low_W  = min(low)  over observed bars [t-W,t)
```

Current M1 bar is excluded.

Record an UP event whenever:

```text
high_t > high_W
```

Record a DOWN event whenever:

```text
low_t < low_W
```

If both occur, record both and set `dual_break=true`.

There is **no outcome-dependent de-duplication and no cooldown**.

Repeated breakout bars remain in the ledger. Their statistical dependence is handled by time clustering rather than deleting observations.

## Pre-event descriptors

Keep continuous:
- directional efficiency;
- non-overlapping range contraction ratio;
- realized-volatility ratio;
- midpoint crossing density;
- boundary age;
- activity ratio;
- spread state.

No balance threshold.

## Outcomes

Continuous path at:

```text
5m / 15m / 30m / 60m / 240m
```

Primary signed resolution is boundary-relative and breakout-direction signed.

Q3 additionally uses remaining movement:

```text
remaining_res_60_after_5 = res_60 - res_5
remaining_res_240_after_5 = res_240 - res_5
```

so early confirmation cannot receive credit for displacement already consumed.

## Q1 — Direction

For every descriptor:
- Spearman relation with signed `res_15`, `res_60`, `res_240`;
- report every symbol/year/direction/scale group;
- summarize median group correlation and sign count;
- do not select the best scale.

Permutation negative control:
- shuffle each descriptor inside `symbol x year x direction x scale x hour-of-day` cells;
- compare observed cross-group summary with shuffled summaries.

## Q2 — Interaction intensity

Only after Q1:
- use `abs(res_h)`, `max(ext_h, inside_h)`, and post-event realized volatility;
- control/report pre-event realized-volatility state;
- intensity predictability is not directional alpha.

## Q3 — Early interaction

Use 5m occupancy/re-entry/path descriptors only to explain movement **remaining after 5m**.
A variable that classifies `res_60` but not `res_60-res_5` is state description, not economic continuation evidence.

## Dependence / uncertainty

Because all breakout bars are retained:
- no IID significance claims;
- uncertainty is block-based;
- primary bootstrap block = `symbol x calendar week`;
- market/year/direction/scale sign stability has priority over tiny p-values.

## Kill conditions

Downgrade/close if:
1. directional relations are unstable across market-years/directions/scales;
2. observed relations are comparable to time-of-day-preserving permutations;
3. effects disappear after obvious volatility/trend controls;
4. only absolute movement/intensity is predictable;
5. early confirmation consumes the remaining payoff.

No strategy authority and no external validation data opening.


## Pre-Q1 instrumentation amendment — 2026-08-27T06:08Z

Added before any Q1/Q2/Q3 outcome analysis because the original descriptor list did not contain an absolute
pre-event volatility control.

Record additionally:
- `rv_current`: realized volatility inside `[t-W,t)`;
- `rv_previous`: realized volatility inside `[t-2W,t-W)`;
- `range_return`: `(high_W-low_W)/close_{t-1}`.

Reason:
`rv_ratio` alone cannot distinguish a low/low regime from a high/high regime with the same ratio.
These fields are causal controls only and are not new strategy signals.


## Pre-Q1 instrumentation amendment 2 — 2026-08-27T06:14Z

Added before Q1 outcome analysis to prevent `balance` variables from proxying an already-established trend.

Record:
- `pre_net_return`: log(close_{t-1}/close_first_in_window);
- `pre_alignment_efficiency`: `break_direction * sum(log returns in W) / sum(abs(log returns in W))`.

The original `directional_efficiency` remains the absolute value.

Primary adversarial control for a claimed balance-direction relationship must include:
- `pre_alignment_efficiency`;
- `rv_current`;
- hour-of-day;
- range/price state where applicable.
