# V9 Deterministic Execution Runtime and Structure Packet Protocol

Date: `2026-09-10`
Status: `ACTIVE DESIGN AUTHORITY / IMPLEMENTATION REQUIRED BEFORE NEXT FUTURE-HIDDEN REPLAY`
Market: `GOLD# ONLY`

## 1. Purpose

V9 needs AI for judgments that cannot honestly be reduced to simple EA rules.

It does not need AI to perform arithmetic, invent support/resistance, decide when an API call occurs, or redraw the market differently each session.

The execution runtime exists to create this boundary:

```text
DETERMINISTIC MARKET FACTS
        ↓
AI DISCRETIONARY JUDGMENT
        ↓
DETERMINISTIC EXECUTION / EVENT MONITORING
```

The goal is lower AI burden and higher cross-session parity, not a more complicated market model.

---

## 2. Core reproducibility principle

Given the same:

```text
raw M1 causal prefix
runtime version
structure-registry version
```

every implementation must generate the same:

```text
structure IDs
price ranges
provenance
current price-to-structure state
Entry/SL geometry
R/S distances
event timestamps
next authorized review time
```

The AI is allowed to disagree on whether the pitch is worth taking.

---

## 3. Structure registry

A structure can have official execution authority only if it is produced by a frozen, versioned definition.

Each structure record must include:

```text
STRUCTURE_ID
STRUCTURE_DEFINITION_VERSION
SOURCE_TIMEFRAME
SOURCE_TIMESTAMPS
LOWER_PRICE
UPPER_PRICE
STATUS relative to current price
```

Optional deterministic metadata may include the source family, for example:

```text
previous-day extreme
previous-week extreme
versioned swing/pivot structure
versioned historical range boundary
versioned breakout/base structure
```

### Critical restriction

This protocol does **not** invent the swing/pivot/range algorithm now.

A structure family is not active merely because its name sounds reasonable. Its exact derivation must be specified, coded, and parity-tested on consumed data first.

Until then it cannot create official SL/TP/review authority.

---

## 4. Liquidity language

OHLC does not reveal actual resting order-book liquidity.

Use `historical price structure` unless depth/order-book evidence exists.

A prior high/low may be a useful structure, but do not claim actual liquidity quantity from OHLC alone.

---

## 5. Deterministic direction facts

Direction fields may be included only when their derivation is explicit.

Examples:

```text
breakout direction relative to structure X
current position above/below structure X
retracement direction relative to a versioned preceding leg
versioned H4/H1 structural direction
```

Do not turn an undefined `Parent trend` label into deterministic runtime authority.

The AI's Parent working belief remains a synthesis, not a code truth.

---

## 6. Canonical market packet to AI

A pre-entry packet should contain only factual/derived information plus a small decision request.

### A. Market facts

```text
cutoff
current price
completed H4/H1 context
completed M15 context if candidate mode
versioned direction facts, if available
```

### B. Structure table

For each active structure:

```text
ID
price range
provenance
current side/distance
```

### C. Candidate geometry

For candidate side(s):

```text
possible falsification STRUCTURE_IDs
deterministic invalidation boundary for each candidate anchor
risk points from current entry reference
risk S
forward structures
points/R/S to each forward structure
```

No AI arithmetic is needed.

---

## 7. Hard SL derivation

The AI chooses the objective structure whose loss genuinely ends the current Child.

The runtime then applies the frozen invalidation-boundary rule for that structure and side.

This rule must be deterministic.

If the system requires a price buffer beyond a zone edge, that buffer must be part of the frozen runtime definition. It cannot be invented per trade by the AI.

Before future-hidden use, exact SL derivation must pass parity testing.

No minimum stop size is implied.

---

## 8. Trade geometry

For a selected anchor:

```text
Entry
Hard SL
risk points = |Entry - SL|
1R = risk points
S = prior completed H4 Wilder ATR14
SL/S
```

For every forward structure in trade direction:

```text
distance points
distance R
distance S
```

These values are descriptive coordinates, not automatic trade gates.

---

## 9. Forward route architecture

Do not force the nearest structure into a semantic label such as `CP1`.

The runtime simply provides ordered forward structures.

The AI may select some of them as review structures.

### Local Bridge

The AI must select one fixed destination ID from the packet before entry.

### Parent-Journey

Fixed TP may remain `NONE`.

At least one relevant forward review structure should normally be selected when such mapped structures exist. All mapped structures remain visible even if not selected.

When a selected review structure is reached, the runtime schedules an AI review. It does not automatically close the trade.

---

## 10. Minimal AI pre-entry request

Ask only:

```text
PARENT_WORKING_BELIEF
STRONGEST_OPPOSITE_CASE
PITCH = TRADE / NO TRADE
SIDE
ATTEMPT_THESIS
SL_STRUCTURE_ID
SCALE
FIXED_DESTINATION_ID if Local Bridge
REVIEW_STRUCTURE_IDS
WHAT_IS_NEW if retry
```

The AI does not need to name:

- memory role;
- repair category;
- Child subtype;
- major/minor resistance class;
- numeric score;
- all market phenomena in prose.

---

## 11. Event scheduler

The local engine continuously processes M1 without large-model calls.

### Mechanical events

```text
Hard SL touch
fixed Local-Bridge destination touch
```

These are resolved directly by chronology.

### Structural review events

A selected mapped structure may generate a review event according to frozen runtime logic such as:

```text
zone touch/entry
zone boundary cross
completed M15 close through boundary
```

The AI chooses which existing structures matter to its current trade; the event detector decides exactly when the chosen structure condition occurred.

### Heartbeats

```text
FLAT: completed H1
SERIOUS CANDIDATE: completed M15
OPEN PARENT-JOURNEY: completed H1 maximum heartbeat
OPEN LOCAL BRIDGE: completed M15
```

For Parent-Journey, an earlier structural event overrides the H1 heartbeat and schedules the next completed M15 review.

---

## 12. Review packet

At a review, provide:

```text
trigger type and timestamp
current price
latest relevant completed bars
favorable/adverse extreme since last review
current position vs mapped structures
any touched/crossed structures
updated MFE/MAE
current R/S mark
```

Ask the AI only:

```text
HOLD / EXIT / REMAP
```

with 1–3 factual evidence lines.

If `REMAP`, the runtime supplies the updated deterministic forward structure table before the next decision.

---

## 13. Profit management objective

The runtime must help avoid two opposite errors:

```text
exit a large winner too early because the first nearby level appeared
vs
ignore meaningful opposing structure until most MFE is returned
```

It does this by calling the AI **at objective mapped structure events**, not by adding a fixed profit rule.

The AI remains responsible for deciding whether the structure was rejected, accepted/consumed, or whether broader progression has deteriorated.

That judgment may differ between AIs. The price packet may not.

---

## 14. Same-side retry protection

After a Hard SL, the runtime preserves the stopped trade's:

```text
side
SL structure ID
stop timestamp
surrounding objective structure state
```

If the AI later wants the same side, it must state one concise `WHAT_IS_NEW` factual change using the current packet.

This is not a retry count rule. It prevents paying repeatedly for the identical attempt without new evidence.

---

## 15. API-efficiency model

The target architecture is not minute polling.

A typical Parent-Journey position may need:

- zero AI calls during quiet minutes;
- one call when a mapped structure event occurs;
- otherwise one H1 heartbeat call.

This is compatible with real API deployment and causal replay.

---

## 16. Cross-AI parity test

At the same consumed-data cutoff, independent runs must match exactly on:

```text
structure table
structure prices/provenance
SL boundary for a given selected structure
R/S geometry
trigger timestamps
review schedule
```

They do not need to match on:

```text
Parent belief
trade/no-trade
selected SL structure
selected review structure
hold/exit decision
```

Those are the explicit discretionary layer.

---

## 17. No future-hidden use before implementation gate

The next future-hidden replay is blocked until:

- active structure families are fully defined;
- parity tests pass;
- event scheduler passes consumed-data tests;
- packet schema is frozen;
- causal reveal tests pass.

Do not spend untouched reserve data to design the runtime.
