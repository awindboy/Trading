# V8 Backlog

Status date: `2026-08-31`
Active phase: `V8-005A MOVEMENT PROBABILITY SHADOW INDICATOR`

## Completed foundation

- [x] Build deterministic causal M1/M5/M15/H1 resampler.
- [x] Build no-future representation/audit harness.
- [x] Implement factual Double-B / M5 MA20 / M5 BB20 event anchors.
- [x] Record unified GOLD source SHA256/coverage.
- [x] Implement event-close-centered price representation.
- [x] Test visual vs exact numerical representation.
- [x] Run numerical/visual/fused/retrieval direction diagnostics.
- [x] Build +/-10p first-passage direction target.
- [x] Add historical indicator sequences and dynamics.
- [x] Run preprocessing tournament including robust normalization and fractional differentiation.
- [x] Add purged chronological label boundaries.
- [x] Test overlap/uniqueness weighting and one-active population.
- [x] Test masked self-supervised reconstruction.
- [x] Test linear / LightGBM / TCN / patch-Transformer model families.
- [x] Test competing-risk direction+time formulation.
- [x] Test event-family and Double-B follow-up direction hypotheses.
- [x] Test rolling / online retraining and simple meta-labeling.
- [x] Separate movement intensity from direction.
- [x] Run movement-probability ablations.
- [x] Build multi-horizon HAR/range-style movement model.
- [x] Build portable 53-feature logistic model for MT5.
- [x] Verify Python-to-MQL formula parity on sampled timestamps.
- [x] Implement MT5 shadow indicator source.

## Immediate runtime validation

- [ ] Compile `mt5/indicators/V8MovementProbabilityIndicator.mq5` in the user's actual MetaEditor.
- [ ] Resolve any compiler warnings/errors without changing the frozen model contract.
- [ ] Confirm GOLD# M1/M5/H1 history depth is sufficient.
- [ ] Verify completed-M5 probability lines display historically.
- [ ] Verify H1 Double-B and M5 MA/BB triangle timing visually.
- [ ] Compare selected timestamps against the parity reference when feed alignment permits.
- [ ] Verify OFF/ON non-interference: no orders, positions or EA state affected.

## Prospective shadow study

- [ ] Create an append-only shadow log for every supported event.
- [ ] Store 15m/30m/60m predicted probabilities before outcome.
- [ ] Store event type and source timestamp.
- [ ] Store human `LONG / SHORT / WAIT / SKIP` decision before outcome.
- [ ] Store actual entry/SL/TP if traded.
- [ ] Store ignored events as well as traded events.
- [ ] Evaluate calibration and score-percentile separation prospectively.
- [ ] Evaluate whether human directional/trading performance improves with movement probability.
- [ ] Do not set a trading threshold until prospective evidence exists.

## Movement-model maintenance

- [ ] Define retraining procedure for 2027 before displaying post-2026 probabilities with authority.
- [ ] Define model-version metadata embedded in the indicator/log.
- [ ] Add optional historical percentile/activity score only if calculated causally from prior data.
- [ ] Investigate broker-feed sensitivity after runtime parity.
- [ ] Test whether live tick activity adds incremental value beyond the current M1 bar-derived portable features.

## Direction branch — paused

Do not spend the next cycle on another isolated RSI/EMA/threshold/architecture variant.

Only reopen autonomous direction research if one of these exists:

- materially new causal information source;
- preregistered new formulation with a different information mechanism;
- prospective human-direction labels that reveal a learnable filtering problem.

## Strategy/campaign research — not yet authorized by movement score alone

- [ ] Only after prospective evidence, test whether movement filtering improves discretionary campaign outcomes.
- [ ] Keep spread/cost/exposure and campaign accounting explicit.
- [ ] Prevent duplicate same-move trade credit.
- [ ] Separate human directional edge from movement-filter contribution.

## Final validation

- [ ] Keep 2022-2026 as open development evidence.
- [ ] Freeze claim-grade movement model and shadow protocol before opening GOLD# 2021.
- [ ] Open untouched 2021 only once under the frozen protocol.
- [ ] Require MT5 runtime/feed parity before any final claim.
