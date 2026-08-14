# Ground Truth V2 Implementation Audit

- Audit date: 2026-08-14
- Authority: `AGENTS.md`
- Pipeline: `4.51-ground-truth-v2`
- Overall status: `CODE COMPLETE / GROUND TRUTH FROZEN`

## Invalidated Ground Truth

- Path: `output/ground_truth_v2_june2026_v451`
- Former manifest claim: `status=FROZEN_GROUND_TRUTH_V2`,
  `groundTruthComplete=true` (`INVALIDATED`)
- Candidate families: 95
- Accepted executions: 2
- Former result: 1 TP, 1 SL, total `+0.1293013556R`
- Status: `INVALIDATED`. A later legally knowable objective on an existing
  physical lineage was absent from the candidate ledger. The former result is
  forensic evidence, not a complete benchmark.
- Engine candidate misses: 0
- Audits: chronological, counterfactual shuffled, daily no-trade MTF,
  trigger-role packet coverage, deterministic stateful PLAN sequence

The frozen ledger is a protocol benchmark, not evidence of profitability. The
negative June result must not be hidden or converted into a positive benchmark.

## Implemented

- Permanent H1/M30/M15/M5 liquidity and displacement evidence ledger, including
  `RAW_SWING`, `REPEATED_DEFENSE`, `RANGE_EDGE`, and `REACTION_TRAP`.
- Root displacement episodes and selectable protected-swing OHLC evidence.
- Lossless deterministic family sub-pages when a PLAN family exceeds the prompt
  limit; no candidate deletion is permitted.
- All PLAN sub-pages for one physical family are collected before a scenario is
  committed. Multiple incompatible approvals across those pages fail closed as
  `PLAN_FAMILY_SUBPAGES_UNRESOLVED`.
- Roots that form before an eligible objective matures remain in the active root
  ledger and are re-evaluated when objective evidence becomes available.
- Ordered current objective family plus at most two inactive long-history H1
  fallbacks. Historical fallback cannot extend an already valid current TP.
- `INTERNAL_ROTATION` pre-consumption cancellation and
  `EXTERNAL_CONTINUATION` intermediate-delivery recording.
- Independent owner epochs, scenario lanes, execution chains, orders, and
  positions. Only `PENDING + FILLED` consumes the maximum three risk slots.
- Opposite-direction concurrent risk, duplicate physical FVG/retest, and
  unresolved lineage are blocked.
- A physical Delivery FVG shared by multiple scenario lineages is blocked before
  semantic review instead of generating duplicate model calls or orders.
- Validated semantic responses are cached by the actual provider request inputs.
  Code-only reruns can reuse an identical decision, while changed evidence,
  contracts, images, model settings, or authority cannot hit that cache.
- HTF OB reaction, Delivery FVG replacement, addon, and post-SL re-entry
  execution-chain handling.
- API and order latency classification, through-delivery handling, frozen spread
  checks, and content-addressed in-flight request recovery.
- Replay and live use the same `advance_closed_m1_bar()` orchestration.
- Adaptive MT5 backfill, DEMO-only router, minimum-lot normalization,
  `order_check`, `order_send`, cancellation, idempotent client IDs, and broker
  reconciliation. Real-account routing remains hard blocked.
- Active Gemini contracts are PLAN, TRIGGER_WATCH, and
  DELIVERY_REVIEW/ADDON. MAP and REFINEMENT are legacy-only and runtime calls
  fail closed.
- Every parsed `AGENTS.md` rule is linked to an executable test ID; contract
  generation fails on missing test references or prohibited legacy phrases.
- Finalization verifies hash-chained audit ledgers, independent provenance,
  packet hashes, role IDs, decision-time availability, order-time evidence,
  global risk exposure, and the persisted external-owner state at PLAN and
  order creation time. Semantic PLAN approval alone cannot freeze Ground Truth.

## Verified Locally

- `python scripts/test_mentor_ai_replay_v4.py`
- `python scripts/test_mentor_ai_replay_v451.py`
- `python scripts/test_ground_truth_v2_integration.py`
- `python scripts/test_mentor_ai_live_v4.py`
- `python scripts/build_mentor_api_contracts.py`
- `npm run build`

## Remaining External Gates

- Real Gemini replay against the corrected stateful June ledger has not yet
  passed. `gemini_v451_gtv2_june2026_incremental_r8_20260814` used the
  superseded four-trade ledger and is legacy evidence only; it must not be
  resumed or compared with the invalidated two-trade Ground Truth.
- Live-shadow event parity against a running MT5 terminal has not been executed.
- Real MT5 DEMO order/fill reconciliation has not been executed.
- Real-account ordering remains disabled and is outside the approval boundary.

Code completion and Ground Truth completion do not imply profitable trading or
Gemini reproducibility. Those claims require their separate external gates.
