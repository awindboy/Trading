# V9 Causal Numeric Analysis and Tooling Protocol

Date: `2026-09-10`
Status: `ACTIVE EXECUTION / ANALYSIS TOOLING AUTHORITY`
Scope: `CAUSAL MARKET INPUT + REVIEW SCHEDULING; NOT A MARKET EDGE`
Market: `GOLD# ONLY`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 1. Canonical input

Official V9 discretionary analysis uses numeric OHLC reconstructed from the verified raw M1 chronological prefix.

Primary fields:

```text
timestamp
open
high
low
close
```

Chart images are supplemental only. Zoom, y-axis scale, visual slope, aspect ratio, and candle pixel size have no independent execution authority.

Any visual claim used for a decision must be restated in exact price/time facts.

---

## 2. Raw-data and clock authority

Use source/broker timestamps exactly as stored.

Do not convert timezones for replay logic.

Do not synthesize missing minutes.

2025 M1 is descriptive price authority, not exact Bid/Ask tick execution authority.

---

## 3. Hard causal-prefix boundary

Official replay must stream the raw file chronologically and stop at the revealed cutoff.

Do not preload the complete future file into an active dataframe and later filter by cutoff.

The helper may inspect only the next row timestamp to determine whether it exceeds the target cutoff; if so, it must not expose that row's future OHLC.

State must contain at minimum:

```text
source path/hash
revealed cutoff
source byte offset
revealed cache
position state
Hard SL / fixed destination if open
review mode
known contamination intervals
runtime/structure version
```

Any accidental future reveal contaminates the exposed interval. Never backfill a trade inside it.

---

## 4. Higher-timeframe construction

Reconstruct completed bars from revealed M1 only.

```text
M15: hh:00-14, 15-29, 30-44, 45-59
H1:  hh:00-59
H4:  00-03, 04-07, 08-11, ...
```

Use completed bars only for normal discretionary review.

Uploaded higher-timeframe files are parity/acceleration aids only after the complete bar lies behind cutoff. Raw M1 wins disputes.

---

## 5. Numeric context windows

Recommended display windows remain bounded perception aids, not trading thresholds:

```text
H4 last 20 completed
H1 last 24 completed
M15 last 16 in candidate/event mode
M5 last 12 only when exact detail is useful
M1 exact local rows for guards/order-of-events
```

The deterministic structure packet may preserve older objective structures outside the visible recent window.

---

## 6. Runtime-derived facts vs AI interpretation

Tooling supplies facts such as:

- exact highs/lows/closes;
- defined structure ranges;
- touch/cross/close state relative to those structures;
- deterministic breakout/retracement labels only when versioned;
- distances in points/R/S.

AI interpretation such as `Parent bullish`, `good pitch`, or `campaign damaged` remains discretionary.

Do not allow discretionary language to alter the causal data boundary.

---

## 7. Replay / AI-call state machine

The causal tool must represent eventual live deployment: the runtime watches price continuously; the AI does not.

### PLANNING / FLAT

An authorized planning call uses completed H4/H1 context plus the deterministic structure packet.

The AI may return:

```text
NO SETUP
or
PRECOMMITTED SETUP(S)
```

Do not call the AI on every completed H1 merely to search for a trade.

A later planning/replanning call requires a frozen planning event or maximum-staleness boundary defined by the active scheduler version.

### SETUP ARMED

Once a setup is armed, advance raw M1 chronologically **without discretionary AI inspection** until the first relevant event:

```text
ENTRY FILLED
SETUP CANCELLED
SETUP EXPIRED
SETUP INVALIDATED BEFORE FILL
REPLANNING BOUNDARY
```

Intermediate M15/H1 candles are processed locally but are not automatically shown to the AI.

If the entry rule itself requires completed-bar confirmation, reveal only the exact completed bar needed by the frozen rule.

### OPEN PARENT-JOURNEY

Local runtime scans M1 continuously for Hard SL and preselected review events.

The next large-model call is the earliest of:

```text
precommitted discretionary review event
maximum-staleness replanning/review boundary
```

A mapped intrahour event may schedule a next-completed-M15 packet when the frozen event rule requires bar completion.

Ordinary M15/H1 completion does not itself require a call.

### OPEN LOCAL BRIDGE

Local runtime guards Hard SL and fixed destination chronologically.

Default behavior is no discretionary AI call between fill and mechanical resolution.

An earlier discretionary review is allowed only if the pre-entry Local-Bridge setup explicitly froze such a review condition.

---

## 8. Heartbeat / maximum-staleness rule

A heartbeat is a fail-safe against an indefinitely stale plan, not the primary observation cadence.

The exact maximum-staleness boundary must be part of the versioned scheduler and justified by the lifecycle scale.

The runtime may cheaply update completed H1/H4 facts without invoking the large model.

The model is called only when:

```text
a precommitted event requires discretionary judgment
or
the frozen maximum-staleness boundary requires replanning
```

This prevents two opposite failures:

- minute/candle polling that manufactures marginal opportunities;
- an old plan remaining armed after its context is no longer valid.

## 9. Mechanical guarded advance

For open positions, already-frozen mechanical events are monitored sequentially in M1 before the requested discretionary review time.

### Hard SL

If Hard SL is first touched before the next review, halt immediately at the first touch M1. Do not reveal later rows in that review interval.

### Local Bridge destination

Guard fixed destination the same way.

If SL and destination occur in the same M1 bar, mark:

```text
INTRAMINUTE_EXECUTION_AMBIGUOUS
```

Do not invent tick order.

---

## 10. Structural review events

Only structures already present in the deterministic packet may create official structural event triggers.

Typical runtime-detectable states include:

```text
zone touched/entered
zone boundary crossed
completed M15 close across configured boundary
selected review structure consumed according to frozen definition
```

The exact event definitions belong to the frozen runtime/structure version.

An AI-only phrase such as `important memory is being tested` cannot itself fire an official event unless it resolves to a mapped `STRUCTURE_ID`.

---

## 11. Entry / pending-order reference

Post-June V9 no longer assumes that entry occurs at the current M1 close when the AI makes a decision.

For a precommitted setup, the planning packet freezes a deterministic `ENTRY_TRIGGER_RULE` and the runtime derives the associated planned order/trigger price according to the frozen execution version.

Replay then advances causally until that condition first occurs. The descriptive fill reference follows the frozen order-simulation rule; it is not hindsight-selected after seeing the move.

For an immediate-entry setup explicitly allowed by a future runtime version, the latest fully revealed M1 close may still be used, but immediate entry is not the default architecture.

Do not use future next-bar opens or hindsight best prices.

---

## 12. S coordinate

Retain:

```text
S(t) = previous fully completed H4 Wilder ATR14
```

S is a distance coordinate only.

Runtime computes:

- SL distance in S;
- each forward structure distance in S;
- realized/MFE/MAE distance in S when useful.

No S threshold creates automatic entry/exit authority.

---

## 13. Parity requirement

Two implementations given the same cutoff and frozen versions must match on:

```text
revealed bars
structure IDs/ranges/provenance
R/S geometry
event timestamps
next authorized review boundary
mechanical guard chronology
```

Different AI trade decisions are allowed. Different factual packets are not.

Label failures specifically:

```text
TOOLING NON-PARITY
STRUCTURE NON-PARITY
GEOMETRY NON-PARITY
EVENT-SCHEDULER NON-PARITY
CAUSAL REVEAL INCIDENT
```
