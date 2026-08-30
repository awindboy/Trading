# V8 Backlog

Status date: `2026-08-31`
Active phase: `V8-A FROZEN / V8-B1 CONDITIONAL DIRECTION PROBABILITY`

## Completed V8-A

- [x] Causal M1/M5/M15/H1 foundation and event ledger.
- [x] Event-close-centered representation audits.
- [x] Visual vs numerical representation research.
- [x] Unconditional +/-10 direction/preprocessing/model falsification program.
- [x] Movement-intensity separation.
- [x] Multi-horizon 10p movement-probability model.
- [x] Portable 53-feature V8-A logistic model.
- [x] Python/MQL equation parity reference.
- [x] MT5 V8-A shadow indicator source.
- [x] Freeze V8-A before V8-B.

## Completed V8-B research

- [x] Align V8-B horizon with V8-A 15m/30m/60m horizons.
- [x] Define conditional side target `P(UP|move,H)`.
- [x] Exclude same-first-M1 ambiguous side cases.
- [x] Generate cross-fitted V8-A scores for direction-feature tests without movement-label leakage.
- [x] Test V8-A probability as direct side feature.
- [x] Test continuous movement-probability gating interactions.
- [x] Falsify both as incremental direction improvements.
- [x] Build signed multi-horizon causal side representation.
- [x] Compare event-only, signed core, magnitude, movement and nonlinear models.
- [x] Run all-event joint UP/DOWN/NO-MOVE validation.
- [x] Run outcome-blind non-overlap evaluation.
- [x] Run week-block bootstrap uncertainty.
- [x] Run event-family falsification.
- [x] Identify H1 Double-B as unsupported direction family.
- [x] Run feature-ablation and permutation negative controls.
- [x] Check movement-probability quintiles vs side predictability.
- [x] Record direct three-class comparison without adopting it.

## Immediate V8-B2 implementation

- [ ] Freeze exact V8-B1 feature equations.
- [ ] Fit/export walk-forward 15m/30m/60m conditional-side model coefficients.
- [ ] Decide whether 15m remains full output or is marked lower-evidence because of early mover scarcity.
- [ ] Implement shadow-only MT5 V8-B extension.
- [ ] Keep V8-A source/model untouched.
- [ ] Display `P(move)`, `P(UP|move)`, joint `P(UP)`, joint `P(DOWN)` distinctly.
- [ ] Suppress V8-B direction on H1 Double-B markers.
- [ ] Verify Python/MQL feature and probability parity.
- [ ] Verify no order/trade side effects.

## V8-A runtime validation still required

- [ ] Compile current movement indicator in actual MetaEditor.
- [ ] Confirm GOLD# M1/M5/H1 history and historical probability lines.
- [ ] Verify event triangles and selected parity timestamps.

## Prospective shadow study

- [ ] Log every supported M5 event, including ignored events.
- [ ] Store V8-A movement probabilities.
- [ ] Store V8-B conditional side and joint probabilities.
- [ ] Store human LONG/SHORT/WAIT/SKIP before outcome.
- [ ] Keep actual trade execution/cost results separate from prediction metrics.
- [ ] Do not tune a trade threshold retrospectively.

## Final validation

- [ ] Keep GOLD# 2021 locked now.
- [ ] Freeze V8-B2 implementation/protocol first.
- [ ] Decide once whether the V8-A/V8-B pair is mature enough to consume 2021.
- [ ] Require MT5 runtime/feed parity before any production claim.
