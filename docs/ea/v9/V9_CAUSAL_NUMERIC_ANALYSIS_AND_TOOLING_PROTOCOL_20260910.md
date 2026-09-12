# V9 Causal Numeric Analysis and Tooling Protocol

Date: `2026-09-10`
Status: `ACTIVE EXECUTION / ANALYSIS TOOLING AUTHORITY`
Scope: `CAUSAL MARKET INPUT + OBJECT GEOMETRY + EVENT REPLAY; NOT A MARKET EDGE`
Market: `GOLD# ONLY`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 1. Dual authority: chart semantics vs numeric execution

Chart images are a primary AI input for semantic market interpretation.

Raw revealed M1 remains the authoritative source for:

- timestamps;
- OHLC;
- higher-timeframe construction;
- exact ICT object coordinates;
- object touch/fill/raid/invalidation timestamps;
- Entry/SL/R/S arithmetic;
- runtime event chronology.

A visual structure selected by AI must resolve to exact objective price/time facts before it receives execution authority.

Visual slope, aspect ratio, zoom, candle pixel size, or freehand box edges have no independent price authority.

## 2. Canonical input and clock

Use source/broker timestamps exactly as stored.
Do not timezone-convert replay logic.
Do not synthesize missing minutes.

2025 M1 is descriptive price authority, not exact Bid/Ask/tick fill authority.

## 3. Fail-closed causal prefix

Official replay streams the raw file chronologically and stops at the revealed cutoff.

Do not preload the full future file into an active dataframe and filter afterward.

The helper may inspect only the next row timestamp to test cutoff.
Do not expose that row's future OHLC when it lies beyond cutoff.

State must retain at minimum:

```text
source path/hash
revealed cutoff
source byte offset
revealed-prefix hash
position state
Hard SL / fixed destination if open
active map/event version
known contamination intervals
runtime/object-engine version
```

Accidental reveal contaminates the exposed interval.
Never backfill a trade into it.

## 4. Higher-timeframe construction

Reconstruct from revealed M1.

```text
M5:  hh:mm buckets of 5 minutes
M15: hh:00-14, 15-29, 30-44, 45-59
H1:  hh:00-59
H4:  00-03, 04-07, 08-11, ...
```

Use completed bars for normal AI decisions unless a frozen runtime event explicitly requires an intrabar fact.

Uploaded H1/H4/M15/M5 files are parity/visual acceleration aids only after the entire referenced bar lies behind cutoff.
Raw M1 wins disputes.

## 5. Chart-native packet

AI-facing research uses two chart roles:

```text
MAP
TRIGGER
```

MAP:

- H1 main chart;
- selected H4/H1 object overlays;
- enough history for the active multi-day map;
- roughly 7-15 trading days as a display default, not a rule.

TRIGGER:

- M5 default;
- M15 when justified by trigger scale;
- local window only after HTF authorization.

Code may generate additional H4 or debug charts for parity/tooling checks.
Do not use them as additional discretionary charts by default.

Annotations must remain concise and must not obscure the price structure.

## 6. ICT candidate-object engine

Official research object geometry must be versioned.

Current engine:

`scripts/v9_ict_object_engine.py`

It reads an already-revealed prefix only.
It never opens future source data.

Current candidate families:

### FVG

Three completed candles.

```text
bull: C1.high < C3.low
bear: C1.low > C3.high
```

Store exact gap edges and source triplet.
`BORN_AT` is C3 completion.
Use M1 after birth for exact first touch and full-fill timestamp.

### Swing/liquidity candidate

Current geometric candidate uses two left and two right bars.
The swing becomes known only after the second right bar completes.

This is a candidate source only.
It has no deterministic major/minor importance.

Use M1 after birth for exact BSL/SSL raid timestamp.

### OB candidate

Current research candidate rule:

- completed bar closes through a confirmed swing candidate;
- last opposite-color candle before that break becomes source-candle candidate.

Store full wick range, body range, Mean Threshold, break reference, break bar, first mitigation, and distal-edge invalidation.

This is a reproducible candidate definition, not proof that every candidate is a meaningful ICT OB.

## 7. Object lifecycle

Code owns geometric state.

```text
FVG: ACTIVE / TOUCHED / FULLY_FILLED
LIQUIDITY: ACTIVE / RAIDED
OB: ACTIVE / MITIGATED / INVALIDATED
```

Store exact geometric end timestamp.
Do not extend a consumed geometric object beyond that timestamp in rendered charts.

AI owns strategic role/state.

```text
SELECTED
SECONDARY
TRANSIT
STALE
RETIRED
DESTINATION
REVIEW
```

Geometric state and strategic state must not be conflated.

## 8. AI selection and exact coordinates

AI selects important objects from the candidate ledger after reading MAP.

Official object geometry is referenced by `OBJECT_ID`.
AI cannot change its stored price range.

If AI identifies an important semantic structure not covered by an existing candidate family, record exact source timestamps and objective coordinates before giving it runtime authority.
Do not use an unversioned freehand box as an executable structure.

## 9. Map ledger

Persist the previous AI map between calls.

Minimum research state:

```text
MAP_VERSION
ASOF
SELECTED_OBJECT_IDS + strategic roles
LONG_SCENARIO
SHORT_SCENARIO
PREFERRED_PITCH / WAIT
ACTIVE_WAIT_EVENT
TRIGGER_STATE
CHILD / POSITION STATE
REVIEW_ROUTE
MAP_CHANGES
```

Every update must state what changed.
Do not silently rewrite old object roles or geometry.

## 10. Event-driven replay

The runtime watches price continuously; AI does not.

### FLAT / PLANNING

AI builds MAP and freezes the next wake event.

### WAITING FOR HTF EVENT

Use `v9_replay_event_runner.py` to advance to the first frozen event.

Supported research events include:

- price threshold;
- zone touch;
- Hard SL / destination;
- frozen completed M5/M15/H1 close condition.

Intermediate rows remain runtime-only until the event.

### TRIGGER ACTIVE

At selected HTF event, render MAP + TRIGGER.
AI may return:

```text
NO ENTRY
WAIT FOR FROZEN TRIGGER
ENTER / ARM CHILD
REMAP
```

If waiting, freeze the trigger before advance.

### OPEN POSITION

Runtime guards Hard SL and selected review/destination events in chronological M1 order.

Ordinary M5/M15/H1 completion does not itself authorize a discretionary call.

At a mapped discretionary review, AI returns:

```text
HOLD
EXIT
REMAP
```

## 11. Mechanical guards

Hard SL first touch halts the Child immediately.
Do not reveal later rows in that guarded interval before recording resolution.

Guard fixed destination the same way when used.

If Hard SL and destination touch inside the same M1 row:

```text
INTRAMINUTE_EXECUTION_AMBIGUOUS
```

Do not invent tick order.

## 12. Entry references

Do not assume current M1 close entry.

A setup freezes an objective trigger/order rule first.
Runtime advances until that condition occurs or is cancelled/invalidated.

For completed-bar confirmation, the descriptive entry reference may be the confirming completed-bar close when that is the frozen research rule.
Do not use hindsight best prices or future opens.

## 13. S coordinate

Retain:

```text
S(t) = previous fully completed H4 Wilder ATR14
```

Use S for distance/scale measurement only.
No S threshold creates entry/exit authority.

## 14. Parity

Two implementations with the same revealed prefix and frozen versions must agree on:

- completed bars;
- object IDs / source / ranges;
- geometric lifecycle timestamps;
- R/S arithmetic;
- frozen event timestamps;
- Hard SL/destination chronology.

Different AI strategic selections are allowed.
Different factual object packets are not.

Label failures:

```text
TOOLING NON-PARITY
OBJECT NON-PARITY
GEOMETRY NON-PARITY
EVENT NON-PARITY
CAUSAL REVEAL INCIDENT
```

## 2026-09-12 dual-clock amendment authority

For semantic strategy/runtime work, also read:

`V9_DUAL_CLOCK_SEMANTIC_RUNTIME_ADDENDUM_20260912.md`

Where this older protocol's single-cutoff assumptions conflict with that addendum, the dual-clock addendum controls.

Runtime must separate:

```text
PRICE_REVEALED_CUTOFF
INFORMATION_KNOWN_AT
```

A next M1 row timestamp may prove earlier M15/H1/H4 buckets complete without exposing the next row's OHLC. Due semantic events must be emitted in deterministic `INFORMATION_KNOWN_AT` order before current-row OHLC is exposed to instant price guards.

Object geometry/source time and object semantic availability time must also be separate. The current H1/H4 object engine's last-M1 label is not by itself sufficient as a strategy `OBJECT_KNOWN_AT`.

Consumed-data research prototype parity:

```text
M15/H1/H4 OHLC mismatch: 0
M15/H1/H4 state mismatch: 0
strategy semantic events: 718
missing: 0
timestamp mismatch: 0
anchor-price mismatch: 0
```

This is an implementation gate, not hidden-data permission.

