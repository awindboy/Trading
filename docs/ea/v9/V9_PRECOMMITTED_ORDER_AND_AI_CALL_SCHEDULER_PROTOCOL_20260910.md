# V9 Precommitted Order and AI-Call Scheduler Protocol

Date: `2026-09-10`
Status: `ACTIVE DESIGN AUTHORITY / IMPLEMENTATION REQUIRED BEFORE NEXT FUTURE-HIDDEN REPLAY`
Market: `GOLD# ONLY`
Production authority: `NONE`
EA authority: `NONE`

## 1. Purpose

V9 does not improve merely because the AI sees more candles or is called more often.

Frequent re-analysis creates a structural risk:

```text
more observations
-> more local explanations
-> more apparent opportunities
-> more marginal swings
```

The desired operating model is the opposite:

> The AI prepares in advance for a small number of worthwhile pitches, expresses them as executable price conditions, and then waits.

The runtime watches price continuously. The large model does not.

---

## 2. Primary operating model

The canonical live/replay flow is:

```text
PLANNING CALL
    ↓
PRECOMMITTED SETUP(S)
    ↓
ORDER ARMED
    ↓
LOCAL RUNTIME MONITORS M1 WITHOUT AI CALLS
    ↓
ENTRY / CANCELLATION / INVALIDATION / EXPIRY EVENT
    ↓
IF FILLED: PRECOMMITTED PROTECTIVE ORDERS BECOME ACTIVE
    ↓
NO AI CALL UNTIL A PRECOMMITTED REVIEW/RESOLUTION EVENT
```

The system must not call the AI merely because another M1/M15 candle completed.

---

## 3. Planning call

A planning call is not an invitation to find a trade at the current price.

Its purpose is to answer:

> What price condition would make a genuinely worthwhile pitch available, if price comes there later?

The deterministic runtime first provides:

- current completed H4/H1 context;
- objective structure table;
- current price;
- exact p/S distance from current price to each structure;
- any deterministic direction facts currently authorized.

The AI may return zero, one, or a small number of `PRECOMMITTED SETUP` records.

`NO SETUP` is a complete and desirable output when no good pitch is prepared.

---

## 4. Precommitted setup schema

Each setup must be executable without a later discretionary entry decision.

Required fields:

```text
SETUP_ID
SIDE: LONG / SHORT
ATTEMPT_THESIS: one concise sentence
SCALE: LOCAL_BRIDGE / PARENT_JOURNEY

ENTRY_CONDITION_TYPE
ENTRY_STRUCTURE_ID
ENTRY_TRIGGER_RULE

SL_STRUCTURE_ID
FIXED_DESTINATION_ID: required for LOCAL_BRIDGE; optional/NONE for PARENT_JOURNEY
REVIEW_STRUCTURE_IDS: optional for PARENT_JOURNEY

SETUP_INVALIDATION_CONDITION
SETUP_EXPIRY_CONDITION
```

The runtime derives all exact prices and geometry from frozen structure definitions.

The AI must not invent undocumented offsets or execution buffers.

---

## 5. Authorized entry-condition families

Entry rules must be deterministic and executable by the runtime.

The initial supported conceptual families are:

### A. Retracement entry

Example concept:

> If price returns to structure X, enter in the prepared direction.

Implementation must specify a frozen order/trigger rule, for example a limit or zone-entry rule defined by the runtime version.

### B. Break entry

Example concept:

> If the lower boundary of structure X breaks under the frozen trigger rule, enter SHORT.

Implementation must define whether the trigger is a price touch, stop-price crossing, completed-bar close, or another deterministic condition.

### C. Reclaim/confirmation entry only if algorithmically defined

Do not use phrases such as `meaningful reclaim` as an executable entry trigger unless the exact condition is frozen and parity-tested.

If it cannot be expressed deterministically, it remains analysis language and cannot arm an order.

---

## 6. Order state machine

The runtime must support at least:

```text
PLANNED
ARMED
FILLED
CANCELLED
EXPIRED
INVALIDATED_BEFORE_FILL
CLOSED_SL
CLOSED_DESTINATION
CLOSED_MANUAL_EVENT_REVIEW
```

An ARMED order waits without large-model calls.

Price may move for minutes or hours without producing a new AI decision.

This is intentional.

---

## 7. Entry-order cancellation and expiry

A precommitted setup must not live forever merely because its entry price has not traded.

Cancellation/expiry must be based on precommitted deterministic conditions, not on the runtime deciding that the chart `looks different`.

Possible families may include:

- opposite structure broken before entry;
- the selected SL/falsification structure is consumed before entry;
- the intended destination is reached before entry;
- a specified higher-timeframe boundary completes and invalidates the setup;
- explicit setup time/session expiry when strategically justified and frozen before use.

Do not create a generic fixed expiry duration merely for convenience.

---

## 8. Protective order packet after fill

When an entry fills, the runtime immediately activates the precommitted risk packet.

At minimum:

```text
Hard SL
```

For a Local Bridge:

```text
Hard SL + fixed destination
```

should normally be expressible as a bracket/OCO-style lifecycle in the execution system.

For a Parent-Journey:

- Hard SL is always active;
- fixed TP may be NONE;
- objective review structures may be preselected;
- the trade is not re-analysed simply because profit grows or another ordinary candle closes.

---

## 9. When the AI is called after entry

The default is **no call**.

The next call occurs only at a precommitted event.

### Mechanical resolution events — no discretionary AI required

```text
Hard SL touch
fixed Local-Bridge destination touch
```

These resolve directly under chronological execution rules.

### Parent-Journey review events

Examples:

```text
selected forward structure reached under frozen event rule
selected adverse structure reached/broken under frozen event rule
precommitted higher-timeframe review boundary
route-map exhaustion requiring REMAP
```

The exact event detector belongs to runtime code.

The AI then answers only:

```text
HOLD / EXIT / REMAP
```

Do not continuously poll the AI between those events.

---

## 10. Heartbeat is fail-safe, not the main strategy

The previous `every H1` convention must not be interpreted as `call the AI every hour forever`.

A heartbeat exists only to prevent an open-ended stale plan when no mapped event occurs.

The preferred hierarchy is:

```text
PRECOMMITTED PRICE EVENT
    before
COARSE HEARTBEAT
```

The exact heartbeat cadence must be justified by the lifecycle scale and implementation tests.

For Parent-Journey it may use completed H1/H4 context, but a new large-model call should occur only if the lightweight runtime detects a material state change under deterministic rules or the frozen maximum-staleness boundary is reached.

Do not introduce minute polling.

---

## 11. Good-pitch discipline

The setup-first architecture is part of V9 strategy discipline, not merely compute optimization.

A good pitch is normally something the trader can describe **before price reaches the entry condition**.

This directly resists:

- chasing every new candle;
- same-auction rapid relabeling;
- seeing more opportunities simply because the AI was called more often;
- entry latency caused by waiting for a large model to analyse a just-happened micro event.

The system should prefer:

> `If price does X at objective structure Y, I am prepared to risk Z.`

rather than:

> `Price just moved; call the AI and ask whether this is a trade.`

---

## 12. Multiple prepared setups

The AI may prepare more than one setup when the market genuinely offers alternative future paths, including opposite-side possibilities.

However:

- each setup must have independent deterministic entry/invalidation conditions;
- order interaction must be specified in advance;
- incompatible setups should use deterministic OCO/cancellation logic when appropriate;
- this must not become a way to place orders everywhere and call every possible move a good pitch.

No target number of setups is authorized.

---

## 13. Replay chronology

Official replay must simulate the same architecture.

After a setup is ARMED:

1. advance raw M1 chronologically without discretionary inspection;
2. stop at the first precommitted relevant event;
3. do not reveal intermediate future candles to the AI merely because they occurred;
4. if the event is an entry fill, activate SL/destination guards immediately;
5. continue to the next precommitted resolution/review event.

This better represents real API deployment than repeated candle-by-candle discretionary calls.

---

## 14. M1 execution limitations

Historical 2025 M1 does not provide exact tick path, queue position, spread/slippage economics, or intraminute order sequence.

Therefore replay must explicitly handle ambiguity when:

- an entry trigger and cancellation condition occur in the same M1;
- entry and SL are both touched in the same M1;
- SL and destination are both touched in the same M1.

Do not invent tick order.

Use an explicit ambiguity label and exclude exact execution claims where ordering cannot be established.

---

## 15. API-efficiency audit

Session/replay logs must include:

```text
number of planning calls
number of candidate/replanning calls
number of open-position review calls
number of minutes/bars monitored locally without AI
number of armed setups
number filled / cancelled / expired / invalidated-before-fill
```

These are process metrics, not optimization targets.

The objective is not minimum API calls at all costs.

It is:

> call the AI only when a genuinely discretionary decision is needed.

---

## 16. What remains discretionary

The AI still decides the parts V9 actually needs AI for:

- Parent working belief and strongest opposite case;
- whether a future conditional setup is a worthwhile pitch;
- which objective structure is the true failure anchor for that attempt;
- Local Bridge vs Parent-Journey scale;
- which objective structures justify future review;
- HOLD / EXIT / REMAP at a scheduled discretionary event.

The AI does **not** need to watch every candle to perform these tasks.

---

## 17. Prohibited regressions

Do not turn this architecture into:

- fixed indicator signals;
- mechanical minimum R;
- mandatory retest count;
- fixed N-loss cooldown;
- placing many speculative orders merely because order entry is cheap;
- an AI call on every M1/M5/M15 candle;
- after-the-fact order placement using a price event already revealed;
- widening SL after fill;
- changing the original setup after seeing adverse/favorable movement unless a precommitted review event authorizes a new decision.

