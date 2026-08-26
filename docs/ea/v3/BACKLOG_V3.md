# V3 Backlog

Status: `PAUSED / V4 ACTIVE`

## P0 — V3-001 raw-data bootstrap

- [x] Freeze V3 research purpose and authority boundary.
- [x] Preserve V1/V2 as controls rather than rewriting history.
- [x] Freeze 2023-2025 as initial discovery data.
- [x] Reserve 2022 as V3 validation vault.
- [x] Keep 2021 untouched.
- [ ] Receive GOLD# 2023-2025 M1 CSV.
- [ ] Validate data coverage, duplicates, gaps, order, spread and precision.
- [ ] Record exact broker/server identity and symbol specification.
- [ ] Build deterministic M1 -> M5/M15/M30/H1/H4 aggregator.
- [ ] Prove bar aggregation against MT5 samples.
- [ ] Build reusable experiment registry.

## P0 — common opportunity universe

- [ ] Implement multiple swing detectors as independent named families.
- [ ] Implement external/internal structure representation.
- [ ] Implement liquidity pool candidate families.
- [ ] Implement zone/FVG/OB candidate families.
- [ ] Implement sweep candidates.
- [ ] Implement local M1/M5 structure-transition candidates.
- [ ] Implement FVG first-retest candidates.
- [ ] Deduplicate correlated scenario fan-out into physical opportunities.
- [ ] Produce annual opportunity-density census for 2023/2024/2025.

## P1 — strategy-family experiments

- [ ] Current V2 chain offline reproduction control.
- [ ] Local-live-swing trigger family.
- [ ] M5/M1 adaptive trigger family.
- [ ] Alternative wave detector family.
- [ ] Expanded liquidity family study.
- [ ] Continuation-only vs reversal vs internal-rotation as separate protocols.
- [ ] FVG selector study: widest / first / nearest / Root-proximal.
- [ ] Session/retest interaction.
- [ ] Natural structural parameter stability analysis.
- [ ] Leave-year-out validation inside discovery panel.

## P1 — feature discovery

- [ ] Build outcome-blind pre-entry feature table.
- [ ] Standardized Fill->+1R/SL labels.
- [ ] MFE/MAE path labels.
- [ ] Regularized linear baseline.
- [ ] Tree/boosting discovery model.
- [ ] Interaction/stability analysis.
- [ ] Distill robust model relationships into interpretable candidate rules.
- [ ] Do not promote a black-box live model by default.

## P2 — exact tick layer

- [ ] Request tick data only for surviving candidate families.
- [ ] Exact same-bar event ordering.
- [ ] Bid/Ask barrier race.
- [ ] Dynamic spread replay.
- [ ] Pending-order fill semantics.
- [ ] Compare fast M1 approximation vs exact tick outcome.

## P2 — independent validation

- [ ] Freeze final candidates before opening 2022.
- [ ] Run 2022 once under frozen definitions.
- [ ] Reject rather than retune failed candidates.
- [ ] Keep 2021 untouched.

## P3 — MT5 promotion

- [ ] Reproduce surviving offline candidate in MT5 Strategy Tester.
- [ ] Require exact real-tick execution integrity.
- [ ] Compare against V2 control.
- [ ] Only then implement/branch a V3 EA.

## V3-003 ??GOLD auction-state reconstruction

### P0 ??state engine

- [ ] Build trailing-only normalized state descriptors.
- [ ] Build causal compression/expansion/reload/exhaustion state representation.
- [ ] Preserve state-transition history without look-ahead.
- [ ] Compare strong/weak-period state composition without creating quarter vetoes.
- [ ] Add naive-control harness to every strategy module.

### P0 ??continuation module

- [ ] Re-express the current selective continuation family as an EXPANSION/RELOAD module.
- [ ] Remove mandatory FVG-retest Entry authority from the active hypothesis.
- [ ] Preserve FVG only as a displacement/context candidate until independently justified.
- [ ] Compare trigger-close / simple pullback execution under the same state.
- [ ] Measure full MFE/MAE path, not only +1R survival.

### P0 ??exhaustion reversal

- [ ] Define objective-delivery / near-delivery state causally.
- [ ] Detect failed continuation / opposite acceptance.
- [ ] Build reversal only inside an exhaustion/failed-auction state.
- [ ] Compare against forced-mirror reversal control.

### P1 ??compression breakout

- [ ] Build causal compression state.
- [ ] Require destination-compatible expansion / acceptance.
- [ ] Compare against generic range-breakout control.

### P1 ??portfolio

- [ ] Evaluate modules independently.
- [ ] Verify opportunity populations are physically deduplicated.
- [ ] Combine only after each module has standalone evidence.
- [ ] Evaluate WR, avg winner, expectancy, DD, streaks and state dependence.

### Governance

- [x] Stop trade-level ML winner/loser mining after cross-year failure.
- [x] Stop fixed momentum-horizon search after leave-year-out instability.
- [x] Demote mandatory FVG-retest Entry after direct falsification.
- [x] Adopt L1 -> L2 -> L3 escalation rule.
- [x] Keep GOLD as the active V3 market.
- [ ] Do not open 2022.
- [ ] Keep 2021 untouched.



## V3-003C — reload state × local acceptance

- [x] Reconstruct a reproducible intermediate-liquidity M5-acceptance control from raw GOLD.
- [x] Reuse the frozen structural-expansion meaning `recent4/prior4 > 1.0` without P/L retuning.
- [x] Add explicit M30/H1 BOS-owner delivery agreement as an alternative delivery-state fact.
- [x] Show that delivery state alone is incomplete.
- [x] Define natural local acceptance dominance: broken-structure acceptance distance > sweep penetration distance.
- [x] Show that local acceptance alone is not an edge.
- [x] Demonstrate the state × acceptance interaction on 2023/2024/2025.
- [x] Compare exact mirror direction.
- [x] Check long/short breadth and quarter composition without creating calendar gates.
- [x] Separate local-trigger invalidation from dynamic delivery-state loss.
- [x] Check zero-spread counterfactual; friction does not explain the interaction.
- [x] Check natural M15/M30 source-scale sensitivity; do not optimize `k` from P/L.
- [x] Keep objective-room context non-authoritative.
- [x] Freeze `V3_RELOAD_CANDIDATE_A` as a development benchmark.
- [ ] Do not modify Candidate A while testing correction-completion / acceptance-persistence variants.
- [ ] Prepare independent 2022 validation contract; open 2022 only under frozen definitions.
- [ ] Reject rather than retune if 2022 reverses the relationship.
- [ ] If independent validation survives, promote to exact-tick replay before MT5 implementation.
- [ ] Keep 2021 untouched.
## V3-003D — dual reload module research (ACTIVE P0)

### P0 — reproducibility first

- [ ] Commit a dedicated Module-L replay script from raw 2023-2025 GOLD M1.
- [ ] Commit a dedicated Module-H replay script from the same raw data.
- [ ] Commit physically deduplicated event ledgers for both modules.
- [ ] Reproduce Candidate-A identity exactly before downstream Module-L/H logic.
- [ ] Reproduce exact mirrors with identical event time and risk.
- [ ] Reproduce natural source-scale / physical-dedupe sensitivity.
- [ ] Record $ / R / M30ATR / D1ATR / time metrics in the same ledger.
- [ ] Do not add a new filter until these current-session results reproduce.

### P0 — Module L: low-R / high-WR

Primary research architecture:

```text
Candidate A virtual failure
-> higher context remains alive
-> correction forms deeper intermediate liquidity
-> atomic same-bar sweep/recovery
-> fresh same-direction M5 re-acceptance
-> first real Module-L Entry
```

- [ ] Reproduce the physically deduplicated deep-requalification population.
- [ ] Keep `min(1R, 0.5 D1 ATR)` and full 1R as explicit checkpoint controls.
- [ ] Keep clean-M1 0.5R / 0.75R only as naive high-WR controls.
- [ ] Reproduce delayed-recovery negative control.
- [ ] Reproduce generic deeper-correction + first-M5-transition negative control.
- [ ] Reproduce exact mirror checkpoint.
- [ ] Test M15 adaptive intermediate source and M15 mentor-wave source independently.
- [ ] Do not add k=1.0-only low-prominence events merely to increase count.
- [ ] Build a failure taxonomy for any Module-L real loss.
- [ ] Expand sample only through semantically independent source evidence, not threshold mining.
- [ ] Keep the initial Candidate-A failure virtual in the primary Module-L design.

### P0 — Module H: high-R / low-WR

Primary research controls:

```text
H0:
Candidate A
-> clean M1 ownership path
-> first broken-M5-level retest
-> same sweep-extreme SL
-> 5R

H1 discovery candidate:
Candidate A
-> clean M1 ownership path
-> first 50% acceptance-leg pullback
-> same sweep-extreme SL
-> +3R then BE
-> final 5R
```

- [ ] Reproduce H0 and H1 with dedicated pending/fill semantics.
- [ ] Keep H0 as the simple control; do not freeze 50% from discovery P/L.
- [ ] Re-run natural 25/50/75/100% pullback variants without threshold optimization.
- [ ] Reproduce 5R exact-mirror advantage.
- [ ] Reproduce actual winner $ / D1ATR / holding-time distribution.
- [ ] Reproduce +3R-BE non-interference with existing +5R winners.
- [ ] Keep +3R 25% harvest as a separate secondary positive-frequency control.
- [ ] Build cross-year failure taxonomy for the 5R losers.
- [ ] Investigate the 2023 loss streak without a 2023-specific veto.
- [ ] Do not lower TP simply to improve H win rate.
- [ ] Keep 10R as a deferred extension until thesis lifetime and holding-cost semantics exist.

### P1 — Module L / H episode interaction

- [ ] Build one episode ledger linking H eligibility/fill/failure to later L requalification.
- [ ] Track cumulative episode risk separately from per-trade R.
- [ ] Test whether H-failure -> L-recovery is repeatable without double-counting exposure.
- [ ] Do not combine standalone P/L until exposure / ordering is deterministic.

### Explicit do-not-repeat list

- [x] Do not replace M5 correction-completion with first M1 transition.
- [x] Do not equate delayed recovery with atomic same-bar rejection.
- [x] Do not restore mandatory FVG-midpoint/retest Entry.
- [x] Do not globally widen SL because higher context survives.
- [x] Do not use generic M1/M5 structural trailing for the final runner.
- [x] Do not use +1R or +2R BE for Module-H 5R runner.
- [x] Do not treat fast +1R as strategic-scale proof.
- [x] Do not treat fixed 10R as a solved structural objective.
- [x] Do not optimize low-R TP fractions from discovery P/L.
- [x] Do not add low-prominence-only source events simply for more trades.
- [x] Do not create quarter / direction vetoes.
- [x] Do not reopen static HTF-state filter mining without new causal evidence.

### Deferred until current dual-module work is complete

- [ ] Compression-breakout module research.
- [ ] Failed-auction / exhaustion reversal module research.
- [ ] Other market-state portfolio expansion.
- [ ] Cross-market expansion.
- [ ] Open 2022 validation vault.
- [ ] Touch 2021.

## V3-003E — replay-complete dual-module improvement backlog

> This section supersedes the unchecked `V3-003D reproducibility first` items above.
> The integrated replay and physical ledgers are now included in the V3-003E package.

### Reproducibility — COMPLETE / VERIFY ON START

- [x] Candidate-A parity reproduced from raw GOLD 2023-2025.
- [x] Module-L physical deep-requalification ledger reproduced.
- [x] Module-H natural pullback panel reproduced.
- [x] Exact-mirror fields reproduced.
- [x] Direct-transfer eligibility fields reproduced.
- [x] BOTH-branch fields reproduced.
- [x] H-to-L recovery links reproduced.
- [x] Descriptive combined episode ledgers reproduced.
- [x] Add integrated `scripts/v3_003e_dual_module_repro.py`.
- [x] Commit immutable V3-003E CSV ledgers.
- [ ] On every resumed session, run parity before new tuning.

### Module L — ACTIVE

Primary:

```text
virtual Candidate-A failure
-> context alive
-> deeper meaningful intermediate M15 liquidity
-> atomic same-bar recovery
-> fresh M5 re-acceptance
-> REAL Entry
-> checkpoint=min(1R,0.5D1)
-> 50% realize
-> residual BE
-> residual +2R
```

- [x] Reproduce 11 physical trades / 11 positive.
- [x] Reproduce 7 residual +2R hits.
- [x] Reproduce exact-mirror checkpoint 1/11.
- [x] Reject generic-pivot sample expansion.
- [x] Reject k=1.0-only low-prominence expansion.
- [ ] Study context/scenario lifetime during long virtual-failure -> L-entry waits.
- [ ] Expand sample only through independent meaningful liquidity semantics.
- [ ] Keep mentor-wave source exploratory until enough unique physical evidence exists.
- [ ] Do not increase full TP to 1.5R/2R merely to raise payoff; it weakened high-WR behavior.
- [ ] Preserve the protected-runner design unless a causal alternative improves it.

### Module H — ACTIVE

Current hierarchy:

```text
H0: clean M1 + broken-level retest
H1: clean M1 + 50% accepted-leg pullback
H2: H1 + direct M1 ownership transfer
H3: H2 + exclude BOTH branch (SHADOW ONLY)
```

- [x] Reproduce H base 48 / 14 TP5 / 31 SL / 3 BE.
- [x] Reproduce direct-transfer 44 / 14 TP5 / 27 SL / 3 BE.
- [x] Reproduce non-direct TP5=0 across natural source/pullback panel.
- [x] Reproduce direct+BOTH TP5=0 across natural source/pullback panel.
- [ ] Do NOT freeze BOTH exclusion until independent evidence resolves the 2025 caveat.
- [x] Preserve +3R->BE as primary protection.
- [x] Keep +3R 25% harvest as secondary positive-frequency variant.
- [x] Reject +1R/+2R BE as primary H runner protection.
- [x] Reject proof-first Entry after original Candidate-A +1R.
- [x] Reject M1-owner-at-fill / pending-flip / extra-M1-rejection gates.
- [x] Reject source-age hard cutoff and correction-start source gate.
- [x] Reject simple opposite-owner veto and directionally-retuned M30-expansion gate.
- [ ] PENDING FIRST: test body-close back through original swept liquidity as strong H invalidation.
- [ ] PENDING SECOND: test +2R existing-50%-fraction protection vs current +3R controls.
- [ ] Continue cross-year remaining-loss taxonomy from H2; H3 stays shadow.
- [ ] Reduce 2023 loss streak without a 2023-specific veto and without deleting TP5 winners.

### H / L episode interaction — ACTIVE P1

- [x] Reproduce five H-loss -> later-L recovery links.
- [x] Reproduce four of five as net-positive under current L payoff.
- [x] Reproduce standalone L non-overlap with H exposure in current sample.
- [x] Produce descriptive combined base and harvest ledgers.
- [ ] Define deterministic cumulative episode risk budget.
- [ ] Define position/exposure ordering for possible H then L.
- [ ] Keep standalone H, standalone L and combined descriptive results separately visible.
- [ ] Do not hindsight-skip H merely because L later appeared.
- [ ] Do not promote combined portfolio before execution/order semantics are explicit.

### Still deferred / forbidden

- [x] No generic M1 early trigger.
- [x] No delayed-recovery equivalence.
- [x] No generic-pivot Module-L expansion.
- [x] No broad SL widening.
- [x] No static HTF threshold mining.
- [x] No quarter/direction vetoes.
- [x] No fixed 10R objective promotion.
- [ ] Do not start compression-breakout module yet.
- [ ] Do not start failed-auction/reversal module yet.
- [ ] Do not open 2022.
- [ ] Do not touch 2021.

## V3-003F — dual reload discovery freeze / validation next

> This section supersedes remaining V3-003E discovery-improvement items for Candidate B.

### Discovery closeout — COMPLETE

- [x] Re-run V3-003E parity from raw GOLD 2023-2025.
- [x] Finish original swept-liquidity M1/M5 body-close H invalidation; reject as immaterial.
- [x] Finish +2R 50%-fraction H protection; reject as primary control.
- [x] Complete natural k x pullback robustness surface without selecting the best point.
- [x] Confirm k=1.5-only low-prominence dilution.
- [x] Cross-check H direct/BOTH/EXP_ONLY/OWNER_ONLY using mentor-wave liquidity semantic.
- [x] Keep H3/BOTH shadow-only because 2025 BOTH evidence is absent.
- [x] Re-run L residual +2/+3/+4/+5 continuation; preserve +2R residual.
- [x] Re-run mentor-wave L physical union; keep exploratory due only two unique additions.
- [x] Audit H/L and H/H active exposure overlap; correct stale non-overlap assumption.
- [x] Freeze same-direction coexistence / opposite-direction block exposure contract.
- [x] Freeze `V3_DUAL_RELOAD_CANDIDATE_B`.
- [x] Write pre-validation contract before opening 2022.

### Research stop rule

- [x] Stop adding 2023-2025 Candidate-B gates, thresholds, direction/session vetoes, or payoff tweaks.
- [x] Keep H3/BOTH outside primary Candidate B.
- [x] Keep mentor-wave L outside primary Candidate B.

### Next — one-time 2022 Level-A validation

- [ ] Verify 2022 GOLD# M1 data identity/coverage without using outcomes to redesign rules.
- [ ] Run frozen Candidate B exactly once.
- [ ] Report PASS / FAIL / INCONCLUSIVE under `V3_003F_VALIDATION_CONTRACT.md`.
- [ ] Do not retune failed thresholds on 2022.
- [ ] Keep 2021 untouched.

### After a 2022 PASS only

- [ ] Exact-tick replay and same-bar ordering.
- [ ] Commission/slippage/swap sensitivity.
- [ ] MT5 Strategy Tester reproduction.
- [ ] Execution parity and only then EA implementation consideration.

## V3-003G — Candidate B 2022 validation failed

### Independent validation — COMPLETE

- [x] Open the pre-registered GOLD# 2022 validation vault exactly once.
- [x] Validate input coverage/duplicates/OHLC/spread.
- [x] Run frozen `V3_DUAL_RELOAD_CANDIDATE_B` without retuning.
- [x] Primary positive-rate criterion FAILED: 25.0% < 50%.
- [x] Average-positive criterion PASSED: +1.458R > 1R.
- [x] Expectancy criterion FAILED: -0.385R < 0R.
- [x] Classify Candidate B as FAIL, not INCONCLUSIVE.
- [x] Record H2, L, H3-shadow, mirror, exposure and H->L diagnostics.
- [x] Mark 2022 as consumed validation.
- [x] Keep 2021 untouched.
- [x] Do not promote Candidate B to exact tick or MT5.

### Explicit no-rescue rules

- [x] Do not insert H3/BOTH exclusion into the failed 2022 result.
- [x] Do not reverse H because the 2022 mirror was stronger.
- [x] Do not create OWNER_ONLY / direction / session / calendar gates from 2022.
- [x] Do not expand L through mentor-wave/generic sources because primary L failed.
- [x] Do not reopen 2023-2025 to refit Candidate B.
- [x] Do not inspect 2021 to rescue Candidate B.

### Next research protocol — NOT YET FROZEN

- [ ] Select a genuinely new discovery allocation before viewing strategy outcomes.
- [ ] Decide whether the next cycle is cross-market GOLD-like suitability research, a later GOLD period, or a new auction-state architecture.
- [ ] Write the new discovery/validation split before strategy selection.
- [ ] Preserve V3-003G as negative authority so failed Candidate-B rules are not silently recycled.

## V4 transition — V3 backlog disposition

- [x] Preserve V3-003G as negative authority.
- [x] Stop Candidate-B rescue/tuning.
- [x] Open V4 as the new active research line.
- [ ] Do not reopen V3 items unless a future decision explicitly allocates a V3 mechanism question.
- [ ] Keep GOLD# 2021 untouched.
