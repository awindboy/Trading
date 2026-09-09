# V9 Research Instructions — Current Authority

Last synchronized: `2026-09-10`
Status: `ACTIVE / JUNE CONSUMED / POST-JUNE SIMPLIFICATION + EXECUTION-RUNTIME FORMALIZATION`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Untouched final temporal reserve: `GOLD# 2021`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 1. Authority and resume order

GitHub is permanent memory. Chat history is only a workbench.

Every V9 session must first refresh latest GitHub HEAD, then read in this order:

1. `docs/ea/v9/AGENTS_V9.md`
2. `docs/ea/v9/HANDOFF_V9.md`
3. `docs/ea/v9/RESEARCH_STATE_V9.md`
4. `docs/ea/v9/V9_TRADING_MINDSET_AND_RESEARCH_GUARDRAILS_20260907.md`
5. `docs/ea/v9/DECISIONS_V9_POSTJUNE_SIMPLIFICATION_AND_RUNTIME_ADDENDUM_20260910.md`
6. `docs/ea/v9/results/V9_JUN25_EXECUTION_ENVIRONMENT_POSTMORTEM_20260910.md`
7. `docs/ea/v9/V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260910.md`
8. `docs/ea/v9/V9_DETERMINISTIC_EXECUTION_RUNTIME_AND_STRUCTURE_PACKET_PROTOCOL_20260910.md`
9. `docs/ea/v9/V9_PRECOMMITTED_ORDER_AND_AI_CALL_SCHEDULER_PROTOCOL_20260910.md`
10. `docs/ea/v9/V9_DISCRETIONARY_TRADING_PIPELINE_POSTJUNE_20260910.md`
11. `docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_POSTJUN_EXECUTION_RUNTIME_20260910.md`
12. current implementation/parity state before any new future-hidden reveal.

April/May/June historical pipeline and contract files remain evidence and history. They do not override the post-June active authority above.

V10 is separate.

---

## 2. V9 permanent trading philosophy

V9 follows the baseball-player principle:

```text
market understanding != direction prediction != good trade
```

The objective is not to correctly predict every next move.

The trader should:

```text
wait for worthwhile pitches
+ accept bounded Child losses
+ tolerate ordinary losing attempts without emotional rescue
+ remain available for the next genuinely good pitch
+ allow a correct large journey to pay for several failed attempts
```

Two or three consecutive stops can be completely acceptable. There is **no** `N-loss stop`, retry cap, cooldown, or required win rate.

However, a long cluster of losses is diagnostic evidence that pitch selection, auction context, falsification scale, or execution environment may be poor. It is not automatically normal merely because V9 tolerates losses.

The payoff architecture must remain asymmetric:

```text
small bounded losses are acceptable
small winners as the default are not the objective
large Parent-Journey winners must be allowed to matter
```

---

## 3. Keep AI discretionary work narrow

V9 uses AI because some judgments are difficult to encode honestly in an EA. It does **not** require the AI to invent the entire market representation.

### Code/runtime owns

- causal M1 ingestion;
- H4/H1/M15 aggregation;
- deterministic price-structure packet;
- exact structure price ranges and provenance;
- Entry/SL distances;
- `R` and `S` geometry;
- forward structure distances;
- pending-entry trigger/order state;
- pre-fill cancellation/expiry/OCO logic;
- Hard SL/fixed-destination bracket guards;
- event timestamps;
- AI-call/review scheduling;
- MFE/MAE and journal arithmetic.

### AI owns only the irreducibly discretionary questions

1. What is the current Parent working belief, and what is the strongest opposite case?
2. What future conditional setup, if any, is a sufficiently good pitch to prepare and risk on if price comes to it?
3. Which **already-mapped objective structure** genuinely falsifies this Child?
4. Is this a Local Bridge or Parent-Journey attempt?
5. When called at a precommitted review/remap event or maximum-staleness boundary, should the position HOLD, EXIT, or REMAP?

The AI must not create official SL/TP/review prices from unversioned language such as `important memory`, `strong support`, `failed-repair origin`, or `major liquidity`.

---

## 4. Parent and Child remain, but Child taxonomy is minimal

Parent remains the larger working belief / journey context. It is never an oracle or direction veto.

Child remains essential because:

```text
Child stop != Parent death
Child win != Parent proof
later same-side movement cannot rescue a stopped Child
```

But Child does **not** require a complex taxonomy.

For execution, a Child only needs:

```text
current paid attempt
side
one-sentence thesis
objective falsification structure
```

Optional terms such as repair, reclaim, hold, departure, memory role, auction relocation, etc. may help explanation but are not mandatory execution fields and do not create price authority.

For a same-side retry after a stopped Child, retain one critical audit question:

> What objective factual change occurred after the previous failure that makes paying risk again worthwhile?

`WHAT IS NEW?` is retained to prevent relabeling the same failed attempt. It is not automatic entry permission.

---

## 5. Hard SL authority

Every new trade has a real Hard SL before entry.

The AI selects the falsification **from objective structures already supplied in the deterministic packet**. The runtime derives the exact boundary according to the frozen structure/runtime version.

When arming a setup record:

```text
ENTRY_CONDITION / planned trigger price
SL_STRUCTURE_ID
Hard SL
planned SL distance points
PLAN_S / planned SL distance S
1R = planned entry-to-SL price risk
```

At fill, record the causal fill reference and `FILL_S` separately.

No stop may be selected because it produces a desirable R multiple.

Do not add:

- fixed point minimum stop;
- ATR stop;
- minimum `SL/S`;
- wider-stop-after-loss rule;
- discretionary undocumented buffer.

A very small SL can be valid if that objective structure truly ends the current Child. For a Parent-Journey attempt using a local anchor, the AI must briefly explain why losing that exact structure ends **this attempt**, not the Parent.

Touch ends the Child. Never widen or rescue it.

---

## 6. Forward structures, TP, and large-winner participation

Permanent June correction:

```text
nearest structure != TP
nearest structure != automatic CP1
nearest structure != entry veto
```

Before entry, the runtime must show all currently mapped forward structures relevant to the trade direction with:

```text
STRUCTURE_ID
price range
source/provenance
distance points
distance R
distance S
```

### Local Bridge

A Local Bridge must choose a real fixed destination from the deterministic structure packet.

### Parent-Journey

A Parent-Journey may have:

```text
FIXED TP = NONE
```

but it still receives the complete forward structure map.

Reaching a mapped opposing structure is primarily a **review event**, not an automatic exit. The AI then judges whether the market is rejecting that structure or accepting/consuming it and continuing.

Do not routinely convert a large Parent-Journey winner into a 5–10 point scalp because the first nearby structure was touched.

Do not add mechanical trailing, BE, partial, or fixed MFE-giveback rules from June.

---

## 7. Prepared-pitch / pending-order environment

The AI/API is not called every minute, every M15, or automatically every H1.

The default flat workflow is:

```text
PLANNING CALL
-> define zero/one/more worthwhile conditional setups
-> ARM executable price conditions/orders
-> local runtime waits without large-model calls
```

A good pitch should normally be describable before its entry price is reached.

The AI is not supposed to stare at every candle until something looks tradable. More observation can create more marginal explanations without creating more genuine opportunity.

Each armed setup freezes:

- deterministic entry condition;
- objective SL structure;
- Local-Bridge destination or Parent-Journey review structures;
- pre-fill invalidation/cancellation/expiry conditions.

After fill:

### Local Bridge

Runtime normally resolves the precommitted bracket lifecycle (`SL` vs fixed destination) without another AI call.

### Parent-Journey

Runtime guards Hard SL and waits for a precommitted objective review/remap event. Fixed TP may remain NONE.

A maximum-staleness heartbeat exists only as a fail-safe; ordinary H1 completion is not automatic large-model work.

Entry and review architecture is governed by:

`V9_PRECOMMITTED_ORDER_AND_AI_CALL_SCHEDULER_PROTOCOL_20260910.md`.

## 8. Minimal pre-entry AI contract

The live AI decision packet should be concise enough that the model spends capacity on the trade, not on filling a compliance form.

Required AI outputs:

```text
PARENT_WORKING_BELIEF        one line
STRONGEST_OPPOSITE_CASE      one line
SETUPS                       NONE or prepared conditional setup(s)
SIDE                         LONG / SHORT per setup
WHY_GOOD_PITCH               concise
ATTEMPT_THESIS               one sentence
ENTRY_CONDITION              deterministic executable condition
SL_STRUCTURE_ID              objective falsification anchor
SCALE                        LOCAL_BRIDGE / PARENT_JOURNEY
FIXED_DESTINATION_ID         Local Bridge only; otherwise NONE
REVIEW_STRUCTURE_IDS         Parent-Journey objective review points
SETUP_INVALIDATION/EXPIRY    pre-fill conditions
WHAT_IS_NEW                  only if retry after a prior failed Child
```

Runtime appends all objective prices, R/S values, timestamps, and provenance automatically.

No mandatory long-form `memory-role`, `repair-type`, `journey maturity`, numeric pitch score, or verbose mirror-check essay.

Bias control is retained through the explicit opposite case and session-level side audit.

---

## 9. Minimal open-position AI contract

At an event or heartbeat, the AI receives current objective facts and answers:

```text
DECISION = HOLD / EXIT / REMAP

PROGRESSION:
- still producing favorable business?
- has opposing movement established enough factual progress to damage the campaign?
- what objective mapped structure was interacted with?

EVIDENCE:
1-3 concise price/settlement facts
```

A Parent-Journey exit must still be based on actual loss of progression, not P/L fear, indicator crosses, or a fixed giveback amount.

---

## 10. Direction and structure parity

Only labels with frozen numeric definitions may be runtime authority.

Examples that can be deterministic **if explicitly versioned**:

- breakout direction relative to a defined structure;
- retracement direction relative to a defined preceding leg;
- previous day/week high/low;
- versioned pivot/range structures;
- price zone touch/cross/close state.

The AI's synthesized Parent working belief remains discretionary.

Do not pretend two AIs will necessarily agree on `important memory`, `major support`, or the exact Child type unless those fields have objective definitions.

---


## 11. Retained May/June corrections that simplification does not remove

Retain these interpretations:

```text
already moved != automatic no trade
nearest forward structure != automatic entry veto
nearby structure != automatic full TP
OPEN ROUTE != permission to ignore mapped structure
new factual event != automatically a good pitch
```

If `too late`, `too extended`, or `not enough room` is used, the AI must state the actual structural reason rather than hiding a minimum-R/no-chase rule.

H1 Stochastic(14,3,3) and EMA9 remain `SHADOW ONLY`. They may be logged, but they do not authorize entry, exit, or review events.

---

## 12. Permanent anti-overfit rules

Do not introduce from June alone:

- N-loss cooldown or max attempts;
- sideways-market veto;
- fixed auction-width filter;
- minimum R;
- minimum SL size;
- fixed ATR/point SL or TP;
- fixed profit lock;
- mandatory partial/BE/trail;
- forced LONG/SHORT balance;
- indicator entry/exit rules;
- fixed hold/retest bar counts;
- automated `Parent says only LONG/SHORT` veto.

June's failure is used to improve **execution control and information quality**, not to hindsight-fit winning rules.

---

## 13. Causal integrity remains non-negotiable

Official replay still uses:

```text
verified raw M1 chronological prefix
-> completed H4/H1/M15 reconstructed causally
-> exact M1 only as needed for guards/execution chronology
```

Never preload the full future dataset into the official discretionary analysis process.

Any accidental future reveal contaminates that interval. Never backfill a trade into exposed data.

`GOLD# 2021` remains untouched final reserve.
