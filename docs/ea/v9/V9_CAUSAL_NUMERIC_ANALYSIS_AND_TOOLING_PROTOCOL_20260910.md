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

## 7. Review state machine

### FLAT

Routine AI heartbeat: every completed H1.

The AI reviews H4/H1 context and decides whether a serious candidate exists.

No need to inspect every M15 while flat.

### SERIOUS CANDIDATE

Immediately switch to M15.

Reveal exactly the next completed M15, then ask the AI again.

Continue M15-by-M15 until:

```text
TRADE
or
NO TRADE
```

Once candidate mode begins, never reveal the rest of the H1 in one step.

### OPEN PARENT-JOURNEY

Local runtime scans M1 continuously for mechanical guards and mapped review events.

```text
next AI review = earliest mapped review event OR next completed H1 heartbeat
```

If a mapped event occurs intrahour, the discretionary review normally uses the next completed M15 and stops there.

If no event occurs, completed H1 is the maximum routine heartbeat.

### OPEN LOCAL BRIDGE

Local runtime guards both Hard SL and fixed destination using M1 chronology.

M15 is the routine discretionary heartbeat until mechanical resolution or earlier structural invalidation.

---

## 8. Why H1 remains but is no longer a blind replay instruction

H1 solves a practical API problem: slow deterioration should not go unreviewed indefinitely.

Therefore H1 is a maximum routine review latency.

It does **not** mean:

```text
always reveal a full hour regardless of what happened inside it
```

Mapped structural events may cause an earlier M15 review.

This preserves API efficiency while allowing important price interactions to be examined promptly.

---

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

## 11. Entry reference

The descriptive entry reference is normally the close of the latest fully revealed M1 at the decision cutoff.

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
