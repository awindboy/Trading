# V7-003A GOLD25 / BTC25 Development Plan

Status: `PREREGISTERED DISCOVERY PLAN`
Date: `2026-08-30`
Markets: `GOLD# 2025`, `BTCUSD# 2025`
Primary chart: `H1`
Raw source: `M1 required/preferred for path and later execution geometry`
Outcome policy: `OUTCOME-INFORMED DISCOVERY ALLOWED`
Validation authority: `NONE`

## Purpose

V7 contains many interacting discretionary ideas.

The goal is not to find the best backtest quickly.
It is to reverse engineer which parts of the Kim Jikseon-style framework carry which information.

> Understand the event before trying to trade it.

## Why GOLD25 and BTC25

The original trader commonly applies the method to Gold, Bitcoin, Nasdaq and Oil.

The first pair is frozen because:
- both are native target markets;
- they differ in session structure and 24/7 behavior;
- two markets are enough to expose market-specific observations;
- adding more markets now creates unnecessary multiplicity.

These market-years will be fully consumed by development.

## Frozen Double-B detector

H1.

Band A:
- period 20;
- standard deviation 2;
- CLOSE.

Band B:
- period 4;
- standard deviation 4;
- OPEN.

An event occurs when one H1 candle reaches/pierces both relevant bands on one side.

Retain:
- UPPER;
- LOWER;
- BOTH/AMBIGUOUS.

Do not silently delete ambiguous events.

## Data-preparation contract

Before outcome subgroup analysis:

1. identify exact raw files;
2. SHA256 every input;
3. record coverage and row counts;
4. check duplicate/non-monotonic timestamps;
5. check OHLC consistency;
6. inspect spread representation and missing/zero rates;
7. document broker/server timezone;
8. derive H1 with one frozen convention;
9. detect all Double-B timestamps;
10. save the complete event census.

The census cannot be edited after outcome analysis begins.

## V7-003A — Double-B Anatomy

No trading objective.

For each event build an anatomy row.

### Pre-event state

Use a fixed 48-H1 descriptive window with 24-H1 summary also available.

Record:
- directional displacement;
- range/trend/transition description;
- causal swing/SR;
- MA20 distance and slope;
- move maturity;
- BB20 width/change;
- BB4 width/change;
- BB4-vs-BB20 relation;
- major session;
- opening-H1 high/low;
- latest session KTR;
- causal same-session KTR rank/percentile.

Do not convert these into a score.

### Event candle

Record:
- side;
- OHLC;
- TR and TR/KTR;
- body and body/KTR;
- body/range ratio;
- close location;
- upper/lower wick;
- band pierce/close state;
- BB20/BB4 width and changes;
- MA20 distance;
- nearby S/R relationship;
- session opening-candle break state.

### Session-break vocabulary

Prefer:

```text
NO_BREAK
WICK_BREAK
CLOSE_BREAK
ACCEPTED_BREAK
FAILED_BREAK
RECLAIM
UNKNOWN
```

Clearly separate what was known at event close from future-confirmed states.

### Future path anatomy — discovery only

Open future.

At minimum record 1h / 4h / 12h / 24h.

Record:
- high-side excursion;
- low-side excursion;
- excursion/KTR;
- time to ±0.5 / ±1 / ±2 / ±3 KTR;
- first meaningful S/R interaction;
- first accepted structural break;
- first failure/reclaim;
- one-stage vs two-stage behavior.

Direction-free anatomy should store high/low excursions separately.
Only use MFE/MAE after a direction hypothesis is explicitly defined.

## Path-family discovery

Do not force BASIC/BREAKOUT/TURNING first.

Allow families such as:
- fresh breakout;
- breakout with pullback;
- failed breakout;
- range-edge fade;
- climactic reversal;
- continuation then turning;
- wick excursion/no acceptance;
- chaotic two-sided expansion;
- no meaningful edge.

Later compress recurring families into the trading vocabulary.

## V7-003B — Context Atlas

Study one dimension at a time.

Priority:
1. session opening-candle behavior;
2. support/resistance;
3. Bollinger geometry;
4. candle anatomy;
5. MA/trend maturity;
6. trendline only if needed.

For every factor identify its job:

| Factor | Event meaning | Archetype | Direction | Entry | SL | TP room |
|---|---|---|---|---|---|---|
| Session | ? | ? | ? | ? | ? | ? |
| S/R | ? | ? | ? | ? | ? | ? |
| Bollinger | ? | ? | ? | ? | ? | ? |
| Candle | ? | ? | ? | ? | ? | ? |
| MA maturity | ? | ? | ? | ? | ? | ? |
| Trendline | deferred | deferred | deferred | deferred | deferred | deferred |

Do not promote a factor from one role to every role.

## V7-003C — KTR Geometry

Only after anatomy/context.

Study:
- current KTR;
- same-session causal rolling KTR distribution;
- KTR percentile/rank;
- high/low excursion/KTR;
- MAE/MFE after direction exists;
- structural invalidation distance/KTR;
- next meaningful target distance/KTR;
- time to KTR barriers.

Questions:
- small KTR: how many KTR of ordinary noise?
- large KTR: how much continuation remains realistic?
- terminal events: different normalized geometry?
- does remaining room explain TP better than raw KTR?

Forbidden:
fixed-table tournaments such as `LOW=3.5/3`, `NORMAL=2/3`, `HIGH=1/2`.

## V7-003D — Entry Architecture

Study only after event meaning:

```text
IMMEDIATE
PLANNED_PULLBACK / ZONE
WAIT_CONFIRM
SKIP
```

BREAKOUT/BASIC/TURNING do not automatically map to one entry style.

## V7-003E — Staging / Risk

Staging is intentionally last.

First create a single-entry baseline.

Then study:
- normal adverse excursion by family;
- expected pullback;
- structurally valid 0.5KTR zones;
- total campaign risk.

Current discovery convention:
each filled leg may independently risk 1R at the common SL.

Always report:
- legs;
- campaign_R_sum;
- maximum campaign stop-risk;
- return / total stop-risk.

Do not use staging to rescue an unplanned losing thesis.

## V7-003F — Freeze

Only recurring findings enter the causal decision rubric.

Before V7-004 freeze:
- event definition;
- chart inputs;
- decision vocabulary;
- confirmation logic;
- KTR use;
- staging rules, if any;
- metrics.

Then choose a new untouched cohort.

## Success criterion

V7-003 does not succeed because discovery P/L is high.

It succeeds if it produces:
- coherent event taxonomy;
- repeatable context interpretations;
- role separation;
- causal definitions that can be locked;
- fewer hindsight degrees of freedom than V7-002.

Profitability belongs to V7-004.
