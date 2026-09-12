# V9 Causal State Machine Implementation Checkpoint

Date: `2026-09-12`
Status: `CONSUMED-DATA CAUSAL IMPLEMENTATION ACCEPTED / FUTURE-HIDDEN STILL LOCKED`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Base GitHub HEAD researched: `d3e62d1733a626f2814d7e720a82c453f36be16e`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`

## 1. What this checkpoint means

The first frozen V9 strategy-extraction grammar has now been implemented as a resumable causal state machine on consumed data.

This checkpoint proves deterministic consumed-data reproducibility and causal event ordering. It does **not** prove future edge, broker-fill parity, production readiness, or EA authority.

The implementation is designed around:

```text
raw authoritative M1
-> timestamp-only discovery of due completed bars
-> emit the complete INFORMATION_KNOWN_AT batch
-> update H4 / H1 / M15 / M5 semantic state
-> resolve live-safe strategy authorization intents symmetrically
-> emit external decision / execution gate when required
-> only then reveal current M1 OHLC to instant price guards
-> persist state-v2
-> resume
```

A semantic gate must be able to stop before the M1 OHLC at the same logical time is revealed.

## 2. Frozen implementation files

```text
scripts/v9_semantic_runtime.py
  SHA256 92f8ab602ca81dff881cb78ee4084664c0c8847fa1948f998bee81158c408c2d

scripts/v9_execution_state_machine.py
  SHA256 8a5430bcecdaad36f47bf63be60fd9f069ed31565037fb025ea4b07fb300fd09

scripts/v9_strategy_state_machine.py
  SHA256 3f7bd38cc17f30409a330b7b357a03685fbf3c05473cc00c9ca536f34136070e

scripts/v9_runtime_state_v2.py
  SHA256 45086e53d34d0c9f247b746ebfbece7ca7e75a453dd888ec1064538527a441cb

scripts/validate_v9_causal_state_machine.py
  SHA256 c3dc7c564251163e14742b0d4acbe676a381446bd4c373f42392f04ab8d5da4b
```

Acceptance evidence is stored under:

```text
docs/ea/v9/results/runtime/V9_RUNTIME_IMPLEMENTATION_ACCEPTANCE_20260912.json
docs/ea/v9/results/runtime/V9_GATE_DRIVEN_MECHANICAL_REPLAY_REPORT_20260912.json
docs/ea/v9/results/runtime/V9_GOLD_CONSUMED_SOURCE_RANGES_20260912.json
```

## 3. Future-hidden source isolation

Normal strategy runtime does not scan the full source to discover consumed ranges.

It requires an exact source-identity + byte-range manifest:

```text
2025H1
  start_offset = 65173328
  end_offset   = 75912993

2026JF
  start_offset = 86972434
  end_offset   = 90428045
```

The manifest is valid only for the authoritative source hash.

Consumed replay revealed exactly:

```text
229,861 M1 rows
```

and revealed:

```text
2025-07 through 2025-12 rows = 0
```

The runtime seeks from the end of the 2025 consumed range directly to the 2026 consumed range. It does not use the hidden interval as a strategy warmup or state input.

The source-index discovery helper is research provisioning only and is not the normal hidden-safe strategy path.

## 4. Dual-clock and information-batch semantics

Persist both:

```text
PRICE_REVEALED_CUTOFF
INFORMATION_KNOWN_AT
```

Same-known-at higher-timeframe completions form one information batch.

Internal calculation order may be deterministic, but strategy authorization is evaluated only after the full due information batch is complete. Python function-call order must not become hidden strategic priority.

Observed consumed example:

```text
CROSS_LANE_CONFLICT_REVIEW
INFORMATION_KNOWN_AT   = 2025-01-17 14:30:00
PRICE_REVEALED_CUTOFF = 2025-01-17 14:29:00
```

The runtime stopped for the semantic decision without revealing the 14:30 M1 OHLC.

## 5. Runtime market-state parity

Fresh raw-M1 replay reproduced the frozen consumed state machinery.

Current acceptance headline:

```text
semantic events: 4,254
revealed consumed M1: 229,861
```

M5 object-known universe:

```text
SWING  12,408
FVG    10,163
OB      5,328
TOTAL  27,899
```

Exact candidate family / direction / source / OBJECT_KNOWN_AT / price geometry mismatch:

```text
0
```

## 6. Critical runtime-statistic correction

The strategy-extraction research used cycle-conditioned statistics that remain valid for their original question:

```text
strict fresh counter M15 transition inside later resolved H1-cycle context: 141
first with-Parent M15 reauthorization inside later resolved H1-cycle context: 94
```

Those counts must **not** be used as the live event universe because the live runtime cannot know whether a future H1 cycle will later resolve.

The live-safe continuous causal universe is:

```text
COUNTER first authorization:     149
WITH_PARENT first authorization: 95
```

Runtime first-origin mismatch versus independent causal audit:

```text
0
```

Runtime first-M5-zone mismatch:

```text
0
```

Therefore retain both number sets with different meanings:

```text
141 / 94 = cycle-conditioned research statistics
149 / 95 = live-safe runtime first-authorization universe
```

Do not rewrite the research history and do not condition live authorization on future cycle membership.

## 7. H1 context compression and gap rule

Trading runtime uses the top-level H1 role:

```text
ALIGNED
INTERRUPT = COUNTERFLOW or LOCAL_BALANCE
```

Descriptive transitions inside interruption such as:

```text
COUNTERFLOW -> LOCAL_BALANCE
```

are not new Child contexts by themselves.

The Atlas `>2h` gap segmentation remains valid for descriptive cycle statistics, but it is **not** a Child invalidation rule. Weekend / market-closure gaps do not create an invented timeout.

## 8. M5 object role and availability

M5 remains execution geometry / location, not direction authority.

The implementation separates:

```text
SOURCE_LAST_M1_AT
OBJECT_KNOWN_AT
```

Object geometry is exact; strategy availability begins only when the object is causally known.

Object selection is block-local. A 2025 archived candidate cannot leak into 2026 execution selection merely because it remains stored for audit provenance.

## 9. Child / order state machine

### Pending entry

```text
M15 authorization
-> freeze structural origin
-> freeze causal M5 location if available
-> CHILD_PENDING
```

Zone touch does not prove a fill:

```text
ZONE TOUCH
-> ENTRY_EXECUTION_REQUIRED
```

Allowed external actions:

```text
ENTRY_FILL
ENTRY_NO_FILL
ENTRY_CANCEL
```

`ENTRY_NO_FILL` returns to pending without inventing a timeout, cooldown, or no-chase distance.

If origin invalidation and zone touch are both present inside the same M1 bar while pending and tick order is unknown:

```text
INTRAMINUTE_ORIGIN_AND_ZONE_AMBIGUOUS
-> fail closed / no fabricated fill
```

### Open Child

Frozen structural origin / Hard-SL guard has deterministic priority over discretionary review.

A stopped Child is dead and cannot be rescued by later movement.

### Journey / Local-Bridge review

With-Parent Child surviving H1 realign may receive:

```text
H1_REALIGN_LAUNCH_ANCHOR
```

Counter Child progressing into H1 interruption may receive:

```text
H1_INTERRUPT_LAUNCH_ANCHOR
```

M1 touch is review evidence.

Completed M15 close beyond the active launch anchor creates one material-damage review for that anchor:

```text
MATERIAL_CHILD_DAMAGE
-> REVIEW_REQUIRED
```

`HOLD` does not repeatedly call the same already-reviewed broken anchor on every later M15 close. A new review lifecycle requires genuinely new review structure.

### Exit / remap

`REVIEW_DECISION = EXIT` creates:

```text
EXIT_EXECUTION_REQUIRED
```

and does not invent a stale semantic-event fill price.

Actual exit requires:

```text
EXIT_FILL
```

Parent authority loss:

```text
PENDING / AWAITING_EXECUTION -> cancel pre-fill Child
OPEN / REVIEW / EXIT_REQUESTED -> REMAP_REQUIRED while structural Hard-SL guard remains active
```

## 10. Cross-lane conflict is fail-closed

Parent remains not a direction veto. Counter and with-Parent Children are both legitimate strategy branches.

However, no consumed-data authority currently decides automatic hedge / netting / replacement when opposite lanes conflict.

Therefore default combined runtime uses:

```text
CROSS_LANE_CONFLICT_REVIEW
```

and does not automatically arm the new opposite Child.

Current deterministic conflict action is only:

```text
SKIP_NEW_PITCH
```

until portfolio conflict policy is separately frozen.

If opposite authorizations occur at the same `INFORMATION_KNOWN_AT`, both intents are deferred until the full batch is known. Neither Python call order nor Counter-first code order receives priority. The runtime arms neither and emits a symmetric conflict review.

## 11. Gate-driven external-decision protocol

Live-style causal command flow:

```text
run-until-gate
-> stop at first external gate
-> write deterministic pending_request.json
-> external execution / review action
-> persist action + state
-> resume
```

Gate kinds:

```text
ENTRY_EXECUTION_REQUIRED
REVIEW_REQUIRED
REMAP_REQUIRED
EXIT_EXECUTION_REQUIRED
CROSS_LANE_CONFLICT_REVIEW
```

Actions must match the frozen first pending gate and its block / Child / known-at identity.

A semantic gate stops before same-time current M1 OHLC reveal. A price gate stops after only the triggering M1 row is revealed.

If an external action creates another gate while an older gate is already queued, the new gate is appended deterministically and deduplicated; it is not silently lost.

## 12. State-v2 restart safety

State-v2 persists at minimum:

```text
source identity / frozen consumed range / byte offset
revealed-consumed hash
PRICE_REVEALED_CUTOFF
INFORMATION_KNOWN_AT
incomplete M5/M15/H1/H4 buckets
EMA / deque / state calculators
active Parent / H1 auction
Counter / With-Parent context and Child state
M5 candidate objects and lifecycle heaps
pending gates
external action log identity
```

Checkpoint is refused inside an incomplete information batch.

Special object-state requirement:

A swing that is no longer geometrically active may still be referenced by the future OB-break candidate heap. Such referenced swing geometry is preserved across restart.

Split-resume replay at multiple consumed checkpoints reproduced uninterrupted ledgers byte-for-byte.

External-action restart replay also reproduced the direct-action run byte-for-byte.

## 13. Gate-driven mechanical acceptance

A full consumed gate-by-gate mechanical harness used synthetic execution reports / review decisions strictly to test interface mechanics.

It is **not** a backtest and its action prices/results have no P/L authority.

Final harness:

```text
segments: 594

ENTRY_EXECUTION_REQUIRED       213
REVIEW_REQUIRED                 81
REMAP_REQUIRED                  28
EXIT_EXECUTION_REQUIRED        109
CROSS_LANE_CONFLICT_REVIEW     162
```

Restart checkpoints were exercised after gate numbers:

```text
1 / 25 / 100 / 250 / 500
```

Final:

```text
revealed consumed rows = 229,861
pending gates          = 0
status                 = PASS
```

Deterministic unit tests:

```text
strategy priority cases: 6 / 6 PASS
gate/runtime edge cases: 3 / 3 PASS
```

## 14. What this checkpoint explicitly does not solve

Remain unresolved:

1. exact broker/tick intraminute fill ordering and executable fill price;
2. final discretionary `HOLD / EXIT / REMAP` policy at review;
3. cross-lane hedge / netting / replacement policy beyond fail-closed review;
4. four observed surviving Counter-Child same-side Parent re-earn handoffs;
5. maximum-staleness and AI-service-outage fail-safe;
6. costs, spread, slippage, and live execution effects;
7. future-hidden validation.

Do not solve these by mining new consumed-data thresholds.

## 15. Next gate

The deterministic causal mechanics gate is accepted on consumed data.

The next work is not more setup mining and not immediate July replay.

Next sequence:

```text
freeze AI review/remap request + response packet
-> freeze AI-call scheduler and max-staleness/service-outage behavior
-> run consumed causal decision dry-run through that exact external-decision protocol
-> freeze implementation bundle / commit / hashes
-> explicitly decide whether the future-hidden replay gate is satisfied
```

Until that explicit decision:

```text
2025-07 = LOCKED
2021    = UNTOUCHED
Production authority = NONE
EA authority         = NONE
```

## 16. 2026-09-12 AI external-decision validation follow-up

<!-- V9_AI_EXTERNAL_DECISION_VALIDATED_20260912 -->

The next-layer packet/scheduler mechanics have now passed consumed validation without modifying this checkpoint's frozen causal core.

```text
segments: 594
AI requests: 109
revealed rows: 229,861
pending gates: 0
gate-driven ledger/action parity: exact
outage/staleness integration: PASS
REMAP action integration: PASS
```

This does not resolve final AI `HOLD / EXIT / REMAP` judgment. The validated request is a causal gate envelope; the chart-native MAP attachment and real semantic decision instruction remain open. `2025-07` stays locked.
