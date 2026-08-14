# Mentor AI Replay V4

## Authority

V4 changes the replay pipeline, not the trading rules. `AGENTS.md` remains the only trading authority.

- V3.25 is read-only legacy and is checked against `config/mentor_ai_replay_v3_25_legacy_manifest.json`.
- V4 never imports a V3 state, schedule, watch event, corrected decision, or resume ledger.
- A profitable response that violates `AGENTS.md` is rejected before an order can exist.
- Every Gemini decision receives the frozen executable rules from `AGENTS.md` plus its phase contract through the API `systemInstruction` field. Sections 13, 16, and 17 contain dated regression answers and are deliberately excluded from model context to prevent benchmark future-data leakage; their general rules are already present in sections 1-12 and remain enforced locally. The dynamic user content contains only the current request and future-hidden chart packet.

## Decision boundary

```text
FLAT
  -> every closed M5 advances indexed root/objective event ledgers (no API)
  -> a root that has no eligible objective remains in the active-root ledger
  -> later objective maturity re-evaluates only those active roots (no API)
  -> a complete newly knowable family wakes one PLAN before source contact
  -> every completed M1 advances directional POI lifecycle locally (no API)
  -> PLANNED with objective/root/full child lineage frozen
  -> parent approach: local chart prefetch only, no API
  -> adaptive final child (M30/M15/M5) touch
  -> local reaction monitor: mature sweep/recovery/body CHoCH candidate
  -> one TRIGGER_WATCH API call
  -> optional same-owner source upgrade selected inside that same call
  -> local execution OB and order geometry
  -> PENDING
  -> first retest FILLED
  -> original SL or TP CLOSED
```

The API returns semantic bar IDs only.

- `PLAN`: direction, scope, range, objective, current-owner protected swing, external-reversal owner-break target/break pair, root OB, displacement, protected swing, and causal child path.
- `TRIGGER_WATCH`: one completed mature-liquidity sweep, its governing M5 correction swing, and the completed meaningful M1 body-CHoCH chain.
- A later causal root/child that forms after PLAN may be offered as a neutral source-upgrade candidate. It can replace the old source only inside the existing TRIGGER_WATCH call, after the new child has actually touched and while owner/objective stay frozen. This does not add an API call.
- The API cannot return state, phase, time, prices, schedules, watch events, entry, SL, TP, or order values.
- PLAN receives the latest completed M1 candle only as `executionReference` and a local `approachEvent`. These are engine-clock and delivery-stage facts, not M1 trigger evidence. They prevent a stale HTF close from being mistaken for the actual price at the decision event.

The local engine owns exact OHLC resolution, touch and invalidation, final sweep, protected swing, body CHoCH, execution OB, spread/stops-aware SL, objective TP, pending fill, and outcome.

## Calls

- An accepted initial scenario has at most two semantic decisions: one `PLAN`, one `TRIGGER_WATCH`; a distinct Delivery FVG execution may add one `DELIVERY_REVIEW`.
- There is no API call from PLAN acceptance until a final-child touch followed by a locally complete sweep/M5/M1 CHoCH candidate.
- There is no API call in `PENDING` or `FILLED`.
- New H1/M15 closes reauthorize frozen invariants locally.
- Every M5 close performs an indexed event check even while another scenario is active. It does not rebuild the whole archive. A newly knowable complete family may call PLAN at formation so its intent exists before either an OB retest or a Delivery-FVG replacement. An incomplete root consumes no API call and remains eligible for a later objective-maturity event.
- A family first discovered on the current candle cannot claim an approach on that candle. An approach that occurs while another scenario is active is recorded as blocked and cannot be resurrected merely because the active scenario closes or cancels later on the same candle.
- The focused PLAN packet retains current H1/M30/M15/M5 context. It does not reduce the chart to old root-formation candles.
- Parent proximal touch is a valid PLAN wakeup because the contract requires the selected final child, not the broad parent, to be frozen before final-child touch. Parent distal consumption or body invalidation expires the candidate locally.
- V4.38 keeps this queue active while a pre-order scenario waits. Same-direction families never cause a second PLAN call. A distinct opposite-direction root may cause one challenger PLAN call only when its own root is approached.
- An accepted non-reversal challenger parks the prior pre-order scenario locally. The prior scenario is restored without API only if its objective, source, owner and untouched final child all remained valid during the parked interval. A child contact that passed while parked makes it stale and permanently discards it. An accepted external reversal replaces the old scenario instead of parking it.
- No challenger call is permitted after final-child contact moves a scenario into reaction monitoring, after an order becomes `PENDING`, or after a position becomes `FILLED`. A valid external reversal first breaks the frozen owner locally, which cancels the old scenario; only then may its approached root schedule a fresh PLAN.
- `summary.json` reports `activeZeroTokenBars`, `flatZeroTokenBars`, candidate refresh/expiry counts, and provider latency. Waiting for a POI consumes no model token.
- PLAN uses event-routed models without adding a reviewer call. A same-direction continuation under an active frozen external owner uses Flash Lite; initial owner establishment, a BROKEN owner, or an opposite-direction family uses Flash. TRIGGER_WATCH also uses Flash and is fail-closed. Authority or trigger quota exhaustion never downgrades to Lite; replay remains resumable and live shadow preserves the same closed bar during exponential zero-token waits.

`OBJECTIVE_REACHED` closes the old external destination but does not erase the owner. A fresh `INTERNAL_ROTATION` may still be planned inside its own newly formed causal dealing range and must use that range's first eligible M15 internal objective. External continuation remains restricted to the existing owner direction, and external reversal still requires the recorded H1/M30 body break.

## Live boundary

Replay and live operation must use the same state engine. Only the market-data adapter changes from a future-hidden NPZ stream to closed MT5 bars/ticks.

- MT5/Python remains online and performs numeric event monitoring. Gemini is not called or kept in a session while price waits between frozen events.
- Charts are rendered only for PLAN and TRIGGER_WATCH requests. Continuous screenshots are forbidden.
- A live feed buffers bars/ticks while an API request is in flight. After the response, a pending order may be placed only if its first retest has not already occurred.
- A retest that occurs before semantic approval returns is recorded as `MISSED_API_LATENCY`; it is never backfilled as a historical fill.
- Objective-first, source invalidation, H1/M15 reauthorization, pending fill, SL, and TP remain local and require no API call.
- Runtime state is persisted after every event so a restart does not re-request the same scenario.
- The persisted state includes parked scenarios and their authority snapshot. Restart restoration therefore does not create an API request or revive a scenario whose decisive event already passed.
- Startup does not call Gemini unconditionally. It rebuilds the local candidate queue and requests PLAN only when the latest closed M1 is already at a valid root approach.

Every request has a content hash covering the system-instruction hash, prompt, dynamic schema, chart hashes, contract hashes, provider, model, output limit, media resolution, and temperature. The stable system instruction is placed before dynamic content so Gemini 3.5+ can use its automatic implicit context cache. A response enters the local shared response cache only after both schema and semantic validation pass. Resume and repeat runs therefore cannot reuse a rejected semantic response.

The shared semantic cache key contains only provider-affecting inputs. A change
to market evidence, system instruction, contract, schema, chart bytes, model, or
generation settings always creates a new request. Implementation-only changes
may reuse a previously validated identical response so replay fixes do not spend
tokens asking the same semantic question again.

When a physical family requires deterministic sub-pages, every page is reviewed
before the family can be committed. Exactly one compatible approved scenario may
survive the aggregate. Zero approvals remain a rejection; multiple incompatible
approvals fail closed as unresolved. A physical Delivery FVG that is claimed by
multiple distinct lineages is likewise blocked before semantic review.

`launchers/Mentor_AI_Live_Shadow.cmd` runs the same state engine against confirmed closed MT5 M1 bars. It is shadow-only: it records decisions but cannot send a broker order. `preflight` checks MT5 connectivity, broker clock normalization, symbol specification, and archive health without calling Gemini.

## 2025-09-01 to 2025-09-05 original-image verification

- The provider received the generated PNG bytes without resizing or re-encoding: PLAN 1540x1320 and TRIGGER_WATCH 1540x990.
- Gemini media processing was `MEDIA_RESOLUTION_ULTRA_HIGH`.
- Flash quota was exhausted, so the completed semantic decisions came from Flash Lite fallback.
- All three known benchmark trades matched direction, fill time, Entry, SL, and TP exactly.
- Two additional trades were produced. An outcome-independent `AGENTS.md` audit using only evidence frozen before each order did not establish a protocol violation in either trade; see the run's `EXTRA_TRADE_AUDIT.md`. The existing truth therefore proves exact known-trade recall but is not currently sufficient to prove exhaustive opportunity parity.
- The replay processed thousands of closed M1 bars between events without API calls. Original-image quality improves evidence fidelity but does not by itself resolve discretionary opportunity selection.

## 2025-09-03 event-driven day verification

- Flash Lite reproduced both executable reference trades exactly, including root, child, objective, Entry, SL, and TP.
- The completed Lite-only diagnostic used 11 calls and 154,393 tokens while 1,368 M1 bars consumed zero tokens.
- It also produced one extra trade. Exact-source Sol independently approved its PLAN but rejected its TRIGGER_WATCH because the body close failed to break the latest post-touch governing M5 correction swing; Lite had selected an older easier-to-break M5 swing.
- This established the production model split: Flash Lite may scout/freeze PLAN, but only Flash may authorize TRIGGER_WATCH. If Flash quota is unavailable, the state waits; it does not trade from a Lite fallback.
- V4.35 then added the latest confirmed pre-break M5 correction guard. A fresh Lite-only day replay completed with both references `EXACT`, `MISS=0`, and `EXTRA=0`; 1,367 M1 bars used no API call. The run used 12 calls and 164,266 tokens.

## 2025-09-01 to 2025-09-05 authority-routing finding

- A V4.35 Lite-only week completed in 50 provider calls and 633,872 tokens, but matched only two of the three legacy executable references and created three different trades.
- The principal failure was PLAN authority selection, not continuous observation. Lite promoted contested `INTERNAL_ROTATION` and `EXTERNAL_REVERSAL` maps, and a long-lived accepted scenario then prevented a later opposite reference from being considered.
- V4.36 therefore routes only owner-establishment and owner-transition PLAN decisions to Flash. Same-owner continuation remains on Lite, so the accepted-scenario contract still uses at most one PLAN call and one TRIGGER_WATCH call.
- The legacy three-trade weekly benchmark is not silently treated as exhaustive: its Sep 4 short conflicts with the later frozen-owner ledger, while prior outcome-independent audits also found omitted AGENTS-supported opportunities. Weekly completion requires an authority-consistent benchmark audit rather than deleting extras to fit the old CSV.

## V4.38 zero-token waiting and weekly diagnostic

- The original-resolution Sep 3 replay again produced two `EXACT` trades with `MISS=0` and `EXTRA=0`. It used 13 semantic requests and 174,293 tokens while 1,366 closed M1 bars required no semantic call.
- A reaction-monitoring scenario no longer permits challenger PLAN calls. The frozen H1/M30 owner must first break locally and cancel the scenario; only then can a new approached root schedule PLAN.
- The Sep 1-5 Lite-only diagnostic completed in 64 semantic decisions, 55 charged provider calls, and 715,372 tokens. It preserved 6,684 zero-token M1 bars, parked eight pre-order scenarios, restored three without API, and discarded five whose decisive event passed while parked.
- Economic parity against the legacy three-trade CSV was `EXACT=2`, `MISS=1`, `EXTRA=5`. This is not a weekly pass. Forty of 54 PLAN responses were accepted, exposing that Lite approves too many formally selectable roots and is not a substitute for Flash owner-authority judgment.
- The omitted legacy Sep 4 short cannot be used as an unquestioned failure target: the current ledger had already frozen a long external owner after the H1 body break. The benchmark and every extra trade require an AGENTS-first, outcome-blind authority audit before weekly parity can be claimed.
- Live MT5 preflight passed with a healthy GOLD feed. A fresh `--once` shadow run and a restart of the same run ID both retained zero semantic requests, zero provider calls, and zero tokens when PLAN permission was set to zero; persisted candidates and the M1 cursor survived restart.

## V4.39 full-map single-plan scheduler

- PLAN is no longer called when an individual mechanical root happens to approach. While FLAT, one closed-H1 event presents every currently viable H1/M30/M15/M5 family together and the model may freeze only one complete scenario. PLANNED, reaction, pending, and filled states cannot schedule another PLAN.
- A new H1 close consumes no token when it contains no unevaluated physical family under the current external-authority key. After PLAN acceptance, child contact, objective reach, source invalidation, owner break, pending fill, and SL/TP are all watched locally.
- The original-resolution Sep 3 Lite replay remained exact: `EXACT=2`, `MISS=0`, `EXTRA=0`. It used 10 provider calls and 193,868 tokens; 1,369 closed M1 bars consumed no semantic call.
- The Sep 1-5 Lite diagnostic used 30 charged calls and 562,576 tokens, down from 55 calls and 715,372 tokens. Against the three known cases it produced `EXACT=2`, `DIRECTION_ONLY=1`, and `MISS=0`.
- The old three-case file was built by concatenating two Sep 3 audits with one isolated Sep 4 case; it was not a sequential review of every valid weekly opportunity. Its coverage is now explicitly `COMPOSITE_AUDITED_CASES_NOT_EXHAUSTIVE`. The three unmatched V4.39 trades are therefore reported as `UNASSESSED`, not `EXTRA`, and an incomplete benchmark cannot pass weekly parity.
- The isolated Sep 4 short is also sequence-inconsistent with the current frozen-owner ledger: the short owner is body-broken before its recorded fill, after which a long external-reversal owner is established. A new sequential, outcome-blind weekly authority audit is required before the weekly target can be honestly accepted or rejected.
- A V4.39 live shadow preflight was healthy. Two starts of `shadow_v439_zero_token_restart_test` preserved the cursor and processed a newly closed M1 bar with zero semantic requests, zero provider calls, and zero tokens when PLAN permission was zero.

## V4.40 causal-refinement routing

- An exact-source Sol audit of the Sep 2 PLAN kept Gemini Lite's direction, external objective, and H1 root, but selected the first causal M5 structure-delivery child instead of Lite's broader M30 child.
- PLAN therefore uses Flash not only for owner establishment/reversal, but also whenever multiple physical families, multiple lineage paths, or competing scenario scopes require semantic arbitration. Lite is reserved for a frozen same-direction owner with exactly one family, one lineage path, and one scope.
- This adds no observation calls while price waits. It changes only which model handles the already scheduled PLAN request, and avoids treating refinement choice as a cheap mechanical task.

## V4.41 scope-correct PLAN contract

- The week-wide independent NO_PLAN audit found two missed opposite-direction `INTERNAL_ROTATION` plans. Both Lite and Flash rejected them for lacking an external-owner body break.
- The root cause was a contradictory dynamic checklist sentence that required every scope to match the intact external-owner direction. This overrode AGENTS.md's explicit rule that an internal rotation may oppose the external owner without becoming an external reversal.
- The PLAN contract now evaluates scopes separately: continuation must follow the owner, reversal requires the recorded external body break, and internal rotation may oppose the owner but must remain inside the active dealing range and use the first mature internal objective.
- A prompt regression test prevents the old all-scopes direction requirement from returning.

## V4.42 explicit scope-owner metadata

- Lite still applied a generic trend-following veto after the V4.41 wording fix. Every PLAN option now carries an engine-derived `scopeOwnerContract` so the model does not have to rediscover the scope rule from prose.
- `INTERNAL_ROTATION` options explicitly state that direction may oppose the active external owner, no external body break is required, and the objective must be the first mature internal liquidity. This metadata does not select an option or authorize a trade; it prevents a valid scope from being rejected for the wrong rule.

## V4.43 deterministic frozen-owner scope

- Historical behavior, superseded by V4.56: the response schema fixed `externalOwnerAndScope` to `PASS` whenever authority existed. This prevented false trend vetoes but also hid genuine owner/scope ambiguity.

## V4.44 fixed-evidence current-contract rejudgment

- `fixed-packet --source-run ... --refresh-current-contract` preserves the exact historical packet, image hashes, and as-of boundary while regenerating only the current phase prompt, system instruction, and schema.
- This separates a contract fix from replay-path drift: the same market evidence can be rejudged without allowing an earlier stochastic PLAN to change the later frozen owner.

## V4.45 internal-rotation scope gate

- Historical behavior, superseded by V4.56: an IR-only packet forced `externalOwnerAndScope=PASS`. V4.56 instead lets Gemini return `FAIL` or `UNRESOLVED` while the engine separately validates the permitted scope relationship.

## V4.46 candidate-set scope gate

- Historical behavior, superseded by V4.56: packets containing any internal-rotation option forced candidate-set scope compatibility to `PASS`. This was removed because it made different target scopes look equally authorized.

## V4.47 quota fallback inheritance

- An empty phase-specific fallback value now inherits `geminiFallbackModel` instead of accidentally disabling fallback.
- Authority PLAN and TRIGGER_WATCH therefore switch from Flash to Flash Lite on HTTP 429 without discarding replay state or adding API calls during the waiting interval.
- Regression coverage verifies immediate 429 fallback and the quota circuit that keeps later requests on the available model.

## V4.48 configurable Sol reasoning

- Codex CLI validation no longer hardcodes `xhigh`; `--codex-reasoning-effort` records `low`, `medium`, `high`, or `xhigh` in the run manifest.
- The default remains `xhigh`. The sequential weekly diagnostic used `medium` to measure model variance without changing Gemini or strategy rules.

## V4.49 transactional PLAN resume

- A PLAN H1 event is marked consumed only after the semantic request returns successfully.
- Token/API budget pauses and recoverable provider failures append `LOCAL_PLAN_REQUEST_DEFERRED` and leave the same H1 event eligible after restart.
- This prevents a live restart from silently skipping the plan that caused the pause.

## V4.52 temporal POI and delivery gate

- Candidate discovery is no longer gated by `FLAT`; root families remain time-stamped and lifecycle-tracked while another scenario waits or trades.
- POI proximity is directional. LONG demand must be approached from above and SHORT supply from below. A bar moving away from a supply/demand source cannot wake PLAN merely because its high/low satisfies a one-sided inequality.
- PLAN's structural reference is the latest completed M5 bar. The exact completed M1 OHLC at the wake event is separately supplied as engine-clock metadata, so the model can see the actual current price without using M1 as scenario or trigger evidence.
- Runtime ordering is candidate refresh and M1 lifecycle first, then active-state processing, then PLAN only when the state was FLAT before the candle. This removes cancellation-then-retrospective-PLAN on one candle.
- Sections V4.39 and earlier above are historical findings. Where their schedulers conflict with this section, V4.52 is the current runtime authority; AGENTS.md remains the strategy authority.

## V4.53 active Delivery FVG execution

- A frozen PLANNED scenario no longer records a valid pre-touch Delivery FVG as shadow-only evidence. When the original final-child path remains untouched and valid, a new destination-direction displacement body-break creates a fresh FVG and causal OB, and the engine atomically creates one `DELIVERY_FVG_REPLACEMENT` first-retest limit order.
- The original deep child path is considered canceled for execution; the engine cannot keep both orders. No additional Gemini call is made because owner, objective, root-child lineage, and execution contract were already frozen.
- The replacement is canceled before fill on objective-first, original source invalidation, protected-swing break, or a body close beyond the fresh FVG. A wick that fills the FVG while the body and causal invalidation hold remains a valid first retest. After fill, only the frozen SL or TP decides the trade.

## V4.54 contract-complete event ledger

- Candidate prices and PD checks use the exact completed M1 event clock. M5 remains the latest structural reference, but its close cannot stand in for the price at a later M1 POI approach.
- PLAN wakeup is the actual root proximal boundary: demand high reached from above or supply low reached from below. The former full-zone-height early-warning offset was removed because it called the model while price was still materially away from the POI.
- Root and child delivery must body-break an actually completed same-timeframe swing. The former fallback that treated any recent candle as a protected swing has been removed.
- H1/M30 dealing ranges are formed only from a completed source swing and a completed objective swing on the same timeframe. Merely containing a lower-timeframe OB or wick no longer creates a protected boundary.
- Every liquidity origin records `matureAtUtc` and `maturityBarId`. The ledger cannot expose a pivot before the second right-hand confirmation candle closes.
- Internal objectives include M5 as well as M15 evidence and are reduced to the first live mature liquidity beyond the final child proximal boundary. The same contract is rechecked at order creation and Delivery FVG replacement.
- A closer live liquidity pool blocks an internal target or Delivery FVG replacement instead of being silently skipped. External continuation keeps its frozen external objective and records nearer pools as intermediate delivery.
- PLAN receives the complete execution contract from AGENTS sections 1-12, 14, and 15. Date-specific regression examples remain outside the model prompt to avoid benchmark leakage.

## V4.55 first-touch event ledger

- A family discovered only after its first root touch is rejected as stale rather than recycled on a later revisit.
- A completed M1 candle that traverses the full root source expires the approach locally and cannot wake semantic PLAN.
- Simultaneous root approaches are sent together in one packet so an arbitrary oldest-family rule cannot hide a competing POI.

## V4.56 owner and scope audit

- `externalOwnerAndScope` can always return `PASS`, `FAIL`, or `UNRESOLVED`; an internal-rotation option no longer forces semantic approval in the response schema.
- A valid same-owner external continuation dominates a same-direction internal target. Internal rotation must state why the external route fails instead of silently shortening TP.

## Validation order

For the one-day Aug 21 benchmark:

1. Run `launchers/Sol_Replay_Run.cmd`.
2. `audit-truth` first proves that every benchmark can exist under the H1 PLAN and later child-touch/trigger chronology.
3. A fixed 2025-08-21 17:00 UTC PLAN packet is judged by the explicitly pinned `gpt-5.6-sol` model, then compared with `AG21-001` map/root/objective/refinement.
4. Sol separately runs the entire closed loop without Gemini.
5. Trade parity must match direction, time, Entry, SL, and TP; `compare-funnel` must also match every executable benchmark and produce no extra order.
6. Only then is `output/mentor_ai_replay_v4_validation/sol_gate.json` written.
7. Run `launchers/Gemini_Replay_Run.cmd` under the identical dataset, rules, code, period, and benchmark-truth hash.

Equivalent weekly launchers are available:

- `launchers/Sol_Replay_Week.cmd` then `launchers/Gemini_Replay_Week.cmd`

The existing Oct 28-31 high-activity truth is intentionally blocked by `audit-truth`: its MAP decisions are not H1 closes and one CHoCH reference forms after the declared sweep. The corresponding launchers stop before any model/API call until a V4-compatible truth replaces it.

Changing `AGENTS.md`, either V4 API contract, the V4 runner/core code, the dataset, or the replay period invalidates the Sol gate before any Gemini request is sent.

## Offline checks

```powershell
python scripts\test_mentor_ai_replay_v4.py
python scripts\mentor_ai_replay_v4.py preflight
```

Expected output:

```text
MENTOR_AI_REPLAY_V4_TESTS_OK
MENTOR_AI_REPLAY_V4_PREFLIGHT_OK
```

## Output

Each run is stored under `output/mentor_ai_replay_v4_runs/<run-id>/`.

- `manifest.json`: provider, exact config, dataset hash, rules hash, and phase-specific system-instruction hashes
- `state.json`: V4-only resumable engine state
- `decision_ledger.jsonl`: append-only hash chain
- `requests/<content-hash>/`: request, schema, `system_instruction.txt`, dynamic `prompt.txt`, and validated response
- `trades.jsonl` and `trades.csv`: closed trades
- `summary.json`: completion, call/token counts, state, trades, and total R
- `parity.csv` and `funnel_parity.csv`: benchmark comparison

An interrupted run resumes in place with `launchers/Gemini_Replay_Resume.cmd`. It retains its original provider and configuration, does not extend follow-through unless explicitly requested, and cannot load a V3 run.

## June 2026 benchmark and long-history objectives

The former June causal ledger is invalidated because discovery provably omitted
a later legally knowable objective on an existing physical family. The binding
rebuild order is documented in `JUNE_2026_BENCHMARK_AUTHORITY.md`.

External destination discovery scans the complete loaded H1 warm-up. Lower-timeframe liquidity remains local to current structure. PLAN receives several reachable external alternatives with age and recent-H1-range context; the model must justify an old H1 destination from current owner and delivery, never from distance or R alone.

V4.51 freezes all valid current-structure H1/M30 objectives as the primary tier and may carry only the two nearest directional H1 pools that are at least 30 days old and still unconsumed as an inactive fallback tier. Historical M30-or-lower levels are forbidden. After Entry and hard SL exist, the engine considers the historical tier only when no current member remains eligible at planned R 1 or greater. Long history never extends an already valid current TP.

## June 2026 benchmark authority

There is currently no authoritative June 2026 Ground Truth. Investigate
evidence exposure, dynamic objective lifecycle, authority state, and model
selection in that order. Do not compare Gemini against the former two-trade
ledger. The rebuild boundary is documented in
`JUNE_2026_BENCHMARK_AUTHORITY.md`.
