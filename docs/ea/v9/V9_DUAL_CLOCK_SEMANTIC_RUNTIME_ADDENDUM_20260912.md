# V9 Dual-Clock Semantic Runtime Addendum

Date: `2026-09-12`
Status: `ACTIVE IMPLEMENTATION GATE / CONSUMED-DATA PARITY PROVEN IN RESEARCH PROTOTYPE`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`
Future-hidden: `2025-07 LOCKED`
Base GitHub HEAD researched: `e3355d6c0de311561390ae4f9ba729f2617d3c35`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 1. Problem

The current causal runtime stores one time-like field:

```text
cutoff == last revealed M1 timestamp
```

That is insufficient for completed-bar semantic events.

A completed M15/H1/H4 bar may become logically known at its scheduled boundary even when the last actual M1 row is earlier because of broker gaps / market closure.

Therefore runtime state must separate price reveal from information time.

## 2. Required dual clocks

Persist both:

```text
PRICE_REVEALED_CUTOFF
= timestamp of the last M1 row whose OHLC is actually revealed

INFORMATION_KNOWN_AT
= logical time at which a completed higher-timeframe bar/state/event becomes known
```

Invariant:

```text
PRICE_REVEALED_CUTOFF <= INFORMATION_KNOWN_AT
```

Do not fabricate missing M1 rows to make the two clocks equal.

## 3. Event ordering

When the timestamp of the next M1 row proves that one or more prior buckets are complete:

```text
1. parse next-row timestamp only;
2. emit all due completed-bar/state events in INFORMATION_KNOWN_AT order;
3. do not inspect next-row OHLC before those semantic events are processed;
4. only then expose current-row OHLC to instant price guards.
```

If several timeframe events share the same known time, use a fixed deterministic ordering and document it. Do not use plan array order as hidden authority.

## 4. Semantic event time is not execution price

A semantic bar/state event may be known at time `T` while the last revealed price row is earlier than `T`.

Therefore:

```text
SEMANTIC EVENT AUTHORITY
!= EXECUTION PRICE AUTHORITY
```

Do not fill at a stale completed-bar close merely because a semantic event fired.

Execution must use a separately authorized executable price event / order mechanism.

## 5. Consumed-data dual-clock parity

Raw authoritative M1 was streamed chronologically without loading hidden future OHLC into the active decision prefix.

Reconstructed bar parity:

```text
M15 bars: 15,339, OHLC mismatch 0
H1 bars:   3,837, OHLC mismatch 0
H4 bars:   1,003, OHLC mismatch 0
```

State parity:

```text
M15 3-view + consensus mismatch 0
H1 3-view + consensus mismatch 0
H4 state mismatch 0
```

Hierarchy parity:

```text
H1 cycles:               186 exact
migration-anchored Parent: 60 exact
same-Parent routes:      120 exact
```

## 6. Strategy semantic-event parity

The consumed-data sequential raw-M1 prototype regenerated the frozen semantic events and compared them with direct answer-sheet computation.

```text
TOTAL semantic events: 718
missing events:           0
timestamp mismatch:       0
anchor-price mismatch:    0
```

Event counts:

```text
H1_INTERRUPT                  171
COUNTER_REAUTH                141
H1_REALIGN                    120
PARENT_REAUTH                  94
PARENT_START                   60
PARENT_END                     58
COUNTER_LAUNCH_DAMAGE          43
WITH_PARENT_LAUNCH_DAMAGE      31
TOTAL                         718
```

This proves deterministic consumed-data reproducibility of the current semantic grammar. It does not prove future edge.

## 7. Observed clock gaps

Typical semantic-event gap:

```text
known_at - price_revealed_cutoff = 1 minute
```

But gaps can be larger around missing-minute / closure intervals.

Observed semantic-event maximums in the current checkpoint:

```text
COUNTER_REAUTH:                1 min
PARENT_REAUTH:                 1 min
H1_INTERRUPT:                  3 min
H1_REALIGN:                    2 min
WITH_PARENT_LAUNCH_DAMAGE:     1 min
COUNTER_LAUNCH_DAMAGE:         1 min
PARENT_START:                  3 min
PARENT_END:                   62 min
```

Broader completed-bar reconstruction previously observed gaps up to:

```text
M15:   6 min
H1:   36 min
H4:  156 min
```

Do not assume `known_at = last M1 timestamp + 1 minute` for all bars.

## 8. Object-engine clock correction

Current GitHub `v9_ict_object_engine.py` defines `Bar.end` as:

```text
bar start + timeframe minutes - 1 minute
```

and uses that timestamp as object `born_at`.

This is valid as a geometric/source last-M1 label but is not sufficient as semantic availability time.

For strategy/runtime use, objects require a separate field such as:

```text
SOURCE_LAST_M1_AT
OBJECT_KNOWN_AT
```

For a normal M5 bar:

```text
SOURCE_LAST_M1_AT = 10:04
OBJECT_KNOWN_AT   = 10:05
```

Research re-ran M5 strategy extraction with this information-known correction.

The exact M5 candidate geometry remained unchanged:

```text
SWING: 12,408
FVG:   10,163
OB:     5,328
```

Adding liquidity candidates from the same swings preserves the earlier `40,307` total candidate universe.

The strategy topology survived the clock correction.

## 9. Required runtime state version change

The current replay state v1 is not sufficient for semantic strategy replay.

A future state version must retain at minimum:

```text
source path / authoritative SHA256
revealed prefix SHA256
PRICE_REVEALED_CUTOFF
INFORMATION_KNOWN_AT
resume byte offset
completed M5/H1/H4 state accumulators or reproducible snapshot reference
active Parent id / side / authority state
active H1 auction state
active Child id / branch / position state
frozen Entry / Hard SL / journey-review anchors
pending-order state
active semantic event-plan version
object-engine version + object known-time convention
contamination intervals
```

Hard SL remains continuously guarded by actual revealed price events.

## 10. Event kinds required before future-hidden replay

The runtime must be able to schedule and emit deterministic semantic events including at least:

```text
PARENT_EARNED
PARENT_AUTHORITY_LOST
H1_INTERRUPT_START
H1_REALIGN
M15_PARENT_REAUTH
M15_COUNTER_REAUTH
H1_LAUNCH_ANCHOR_TOUCH / DAMAGE
M15_CLOSE_BEYOND_LAUNCH_ANCHOR
PENDING_ORDER_INVALIDATED
CHILD_HARD_SL
CHILD_FILLED
REMAP_REQUIRED
```

Names may change in implementation, but semantics must not.

## 11. Hidden-data gate

The parity result is an implementation milestone, not permission to unlock July.

Before hidden replay:

```text
- merge a versioned dual-clock runtime implementation;
- extend M5/M15 object availability convention in code;
- replay consumed periods sequentially through the actual implementation;
- verify exact event/order/SL/review priority;
- freeze implementation commit and hashes;
- confirm no open parity gate remains.
```

Until then:

```text
2025-07 = LOCKED
2021 = UNTOUCHED
```
