# V9 AI Review / Remap Packet + Scheduler Protocol

Date: `2026-09-12`
Status: `AI GATE-ENVELOPE / SCHEDULER MECHANICS FROZEN + CONSUMED PARITY PASS / CHART-NATIVE DECISION INPUT STILL OPEN`
Production authority: `NONE`
EA authority: `NONE`
Market: `GOLD# ONLY`
Base GitHub HEAD: `395cef95046226d1814466475dda200901e0046d`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
Future-hidden: `2025-07 LOCKED`
Untouched reserve: `GOLD# 2021`

## 1. Purpose

The deterministic causal state-machine mechanics gate is already accepted on consumed data.

This protocol freezes the next external-decision layer without adding a new market filter:

```text
accepted causal state machine
-> deterministic gate routing
-> exact AI request packet for semantic review/remap only
-> exact response validation
-> structural-staleness rejection
-> service-outage fail-stop
-> external action through the existing first-pending-gate runtime
```

This document does not define a new trading edge and does not authorize hidden replay. The request defined here is the deterministic causal **gate envelope**. Under current chart-native authority, a real AI semantic decision still requires a separately frozen causal MAP attachment and decision instruction contract.

## 2. Versioned protocol

```text
REQUEST_VERSION   = v9-ai-review-remap-request-1
RESPONSE_VERSION  = v9-ai-review-remap-response-1
SCHEDULER_VERSION = v9-ai-call-scheduler-1
STALENESS_VERSION = v9-structural-staleness-1
OUTAGE_VERSION    = v9-ai-outage-fail-stop-1
```

Implementation:

```text
scripts/v9_ai_decision_protocol.py
scripts/validate_v9_ai_decision_protocol.py
scripts/tests/test_v9_ai_decision_protocol.py
```

## 3. Scheduler routing

AI is not called continuously.

The first pending causal gate is routed by type:

```text
ENTRY_EXECUTION_REQUIRED
EXIT_EXECUTION_REQUIRED
    -> EXECUTION_ADAPTER

REVIEW_REQUIRED
REMAP_REQUIRED
    -> AI_DECISION

CROSS_LANE_CONFLICT_REVIEW
    -> DETERMINISTIC_FAIL_CLOSED
       CONFLICT_DECISION = SKIP_NEW_PITCH
```

Ordinary M1/M5/M15/H1 completion does not call AI by itself.

The scheduler does not give AI authority over broker fill reports.

## 4. AI request packet

A request can only bind to the exact first pending gate.

The packet contains only currently causal state:

```text
gate identity / kind / known_at / block / branch / Child
PRICE_REVEALED_CUTOFF
INFORMATION_KNOWN_AT
source identity + revealed-prefix identity
semantic / lane / object / action log hashes
Parent snapshot
latest H4 / H1 / M15 / M5 state
current H1 / M15 relation
last actually revealed M1
active lane context
active Child snapshot
structural origin / Hard-SL guard
frozen execution-zone identity / geometry
journey role / launch anchor / damage reason
```

The packet does not include future price or later outcome.

## 5. Response semantics

### `REVIEW_REQUIRED`

Allowed semantic decisions:

```text
HOLD
EXIT
REMAP
```

Runtime mapping:

```text
HOLD  -> REVIEW_DECISION(HOLD)
EXIT  -> REVIEW_DECISION(EXIT)
REMAP -> REVIEW_DECISION(REMAP)
         -> new REMAP_REQUIRED gate
```

A review response cannot directly invent new Parent coordinates.

### `REMAP_REQUIRED`

Allowed semantic decisions:

```text
EXIT
REMAP
```

`REMAP` requires:

```text
new_parent_id
new_parent_side = UP / DOWN
journey_role
```

and maps to the existing `REMAP_RESULT` runtime action.

Free text may be stored as non-authoritative notes later, but only the versioned semantic fields have action authority.

## 6. Maximum-staleness behavior

Do not create a fixed `N minutes` market threshold.

The frozen policy is structural exactness:

```text
response is valid IFF
same first pending gate_id
AND same request fingerprint
AND same causal-prefix hashes / clocks
AND same Parent / Child / context snapshot
```

Any mismatch means:

```text
REJECT RESPONSE
-> rebuild current request
```

Therefore elapsed wall-clock time by itself is not market authority.

## 7. AI service outage

The outage policy is:

```text
FAIL_STOP_GUARDED
```

An outage does not invent:

```text
HOLD
EXIT
REMAP
timeout
cooldown
```

During an unresolved semantic AI gate:

```text
no new risk
no implicit semantic market decision
semantic replay does not advance through the unresolved gate
precommitted Hard-SL remains external/runtime authority
```

The live execution/risk adapter must remain independent of the large-model service. Offline causal replay pauses at the gate rather than fabricating latency price history.

## 8. Cross-lane conflict

Current authority still has no automatic hedge/netting/replacement policy.

Therefore:

```text
CROSS_LANE_CONFLICT_REVIEW
-> SKIP_NEW_PITCH
```

remains deterministic and does not require an AI call.

## 9. Validation acceptance

Local/static acceptance:

```text
strategy priority cases: 6 / 6 PASS
gate/runtime edge cases: 3 / 3 PASS
AI protocol unit cases:   8 / 8 PASS
```

Covered:

```text
scheduler routing
packet determinism
prefix/Child fingerprint sensitivity
review response mapping
remap required fields
stale response rejection
outage no-market-decision behavior
cross-lane deterministic skip
Hard-SL priority
request/restart exactness
```

## 10. Consumed causal dry-run — PASS

`scripts/validate_v9_ai_decision_protocol.py` was executed against the authoritative M1 and frozen consumed byte-range manifest.

Synthetic response policy:

```text
REVIEW_REQUIRED -> EXIT
REMAP_REQUIRED  -> EXIT
```

This mirrors the older mechanical harness only to test interface mechanics. It has no strategy-quality or P/L authority.

Result:

```text
segments                         594
ENTRY_EXECUTION_REQUIRED         213
REVIEW_REQUIRED                   81
REMAP_REQUIRED                    28
EXIT_EXECUTION_REQUIRED          109
CROSS_LANE_CONFLICT_REVIEW       162
AI semantic requests             109
revealed consumed rows       229,861
pending gates                      0
request restart parity           PASS
status                           PASS
```

The AI-layer replay was byte-identical to the accepted combined gate-driven mechanical baseline for all factual/action ledgers, including `external_actions.jsonl`.

Frozen combined gate-driven hashes:

```text
revealed_consumed.tsv  ddc7e6d8a280a0e14258dbfe5e891caf816d85f42bf60d87db4b1855b640334a
semantic_events.jsonl  6844da62c01f70f609f305040712f174fa1f432164d13f5e6109ad4a296e1506
counter_events.jsonl   e6a26ef44acac1078d9dd496f591ffc1c17896b264d4e07adb7ebb28d63e9932
with_parent_events.jsonl 6bdf8152a12b2c5342f8ff7aa04c1b7d46c57a437279ca83f52e2b681991bff2
object_known.jsonl     ffaae63cc13a3a981ab587b22b36c2e882bc2bb086f766dff537f8fd0b98d326
external_actions.jsonl 236809d1566033419600528bb131d9ba3de81779dbc0150b560ff855311ce218
```

Important correction: the initial validator draft incorrectly compared combined gate-driven lane logs with older `independent_lanes=True` full-run hashes. The accepted 594-gate mechanical baseline was rerun, and the correct combined-action hashes above were frozen. The packet/scheduler run matches that correct baseline exactly.

## 11. Actual-gate safety integration

Actual consumed gates were used to verify the interface beyond synthetic unit objects.

First tested `REVIEW_REQUIRED`:

```text
gate_id                    b0d82335f3929e41f25e7c95
outage state mutation      NO
restart request exact      YES
stale response rejected    YES
new risk during outage     NO
semantic advance on outage NO
Hard-SL origin retained    YES
```

First tested `REMAP_REQUIRED`:

```text
gate_id                    33457bd70777a180dcc24aec
old Parent                 2025H1-MP003
current causal Parent      2025H1-MP004 / UP
synthetic REMAP result     OPEN / WITH_NEW_PARENT_JOURNEY
structural origin changed  NO
pending gate after action  NONE
```

This proves the action path, not that a real AI should choose REMAP in that case.

## 12. 2024 tick execution validation

The supplied 2024 tick archive was audited separately from strategy-development data.

Archive identity:

```text
Desktop(3).zip
SHA256 aab45d9509198b0172857ea9bf45ed7a230d3dcf5b039075925fd0007a1b69c2
```

Scope:

```text
12 tick files
51,063,932 tick rows
41,254,944 BID updates
344,185 reconstructed M1 bars
2.098 GiB uncompressed tick data
```

Against authoritative M1:

```text
OPEN/HIGH/LOW/CLOSE/TICKVOL mismatch = 0
M1 minute missing tick minute         = 0
tick minute missing authoritative M1  = 0
timestamp backward movement           = 0
```

There are `632` duplicate tick timestamps. They do not move time backward and do not break M1 parity; their source sequence must be retained rather than timestamp-deduplicated.

Intraminute final-extrema order:

```text
HIGH before LOW: 170,555
LOW before HIGH:  173,489
FLAT:                 141
```

The near-even order supports the current fail-closed treatment of M1 intraminute ambiguity.

Observed descriptive spread by month is typically around:

```text
median ~ $0.20 - $0.23
p95    ~ $0.29 - $0.34
```

with observed monthly maxima up to `$2.35`. These are historical execution-environment observations, not strategy thresholds.

Weighted local tick-audit throughput was about `11.02 MB/s` over the supplied 2.098 GiB uncompressed data.

Evidence:

`docs/ea/v9/results/runtime/V9_2024_TICK_M1_EXECUTION_AUDIT_20260912.json`

## 13. Chart-native AI input remains an explicit blocker

Current causal tooling authority states that chart images are a primary AI input for semantic market interpretation.

The validated request v1 freezes:

```text
causal gate identity
causal prefix identity
Parent / H4 / H1 / M15 / M5 semantic state
Child / origin / zone / launch-anchor state
response schema
staleness / outage behavior
```

but it does **not** yet freeze the chart-native `MAP` attachment or the exact AI semantic decision instruction/model-role contract.

Therefore this v1 packet should be read as the frozen deterministic **AI gate envelope**, not yet the complete live AI input authority.

A future chart attachment must be bound to the same causal request fingerprint and must not expose any row beyond `PRICE_REVEALED_CUTOFF`.

## 14. What remains unresolved

1. final strategy-quality judgment among AI `HOLD / EXIT / REMAP`;
2. chart-native review/remap `MAP` attachment contract;
3. exact AI semantic prompt / model-role contract;
4. exact 2025/2026 tick/broker fill ordering because tick truth supplied here is 2024;
5. cross-lane hedge/netting/replacement beyond fail-closed skip;
6. four same-side Parent re-earn handoffs;
7. future live spread/slippage/cost behavior;
8. future-hidden strategy performance.

Do not solve these by mining hidden thresholds.

## 15. Future-hidden gate decision

```text
2025-07 FUTURE-HIDDEN GATE = NOT SATISFIED YET
```

The packet/scheduler mechanics gate passed, but synthetic EXIT decisions do not freeze the real discretionary AI path. Under the active chart-native authority, the MAP attachment and actual AI semantic-decision contract must be frozen before future-hidden replay is treated as a valid strategy test.

## 16. Next order

```text
packet/scheduler mechanics accepted
+ 2024 tick execution-source audit accepted
-> freeze chart-native review/remap MAP attachment
-> freeze actual AI semantic instruction / model-role contract
-> consumed real-input AI decision dry-run
-> freeze packet/chart/prompt/model-role hashes
-> explicit future-hidden gate decision again
```

Until then:

```text
2025-07 = LOCKED
2021    = UNTOUCHED
Production authority = NONE
EA authority         = NONE
```

## 2026-09-13 scheduler research extension from 2024 loss postmortem

<!-- V9_2024_LOSS_POSTMORTEM_20260913 -->

The accepted v1 `REVIEW_REQUIRED / REMAP_REQUIRED` envelope remains mechanically valid. 2024 losses show, however, that most Hard-SL failures occur before those semantic gates can act (`152 / 153` Hard-SL trades had no prior AI semantic review).

Therefore the next research may evaluate **candidate** chart-native semantic events before changing scheduler authority:

```text
ENTRY_CONTEXT_REVIEW     (candidate only)
DELIVERY/PROGRESSION_REVIEW (candidate only)
```

Neither is authorized yet. Their event authority, exact causal chart attachment, action schema, and winner-preservation behavior must first be demonstrated on consumed data.
