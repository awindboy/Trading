# V8 Decisions Addendum — V8-A2 Movement Reliability — 2026-09-01

This file continues `DECISIONS_V8_ADDENDUM_20260901.md` from D-V8-066 onward.

## D-V8-066 — Keep frozen V8-A as the movement authority after A2 research

Date: `2026-09-01`

Decision:

Do not replace or modify the current V8-A MT5 model/indicator as a consequence of the first V8-A2 tournament.

Reason:

V8-A2 produced repeatable but modest ranking improvements. No challenger demonstrated enough future-year improvement, calibration quality and prospective evidence to justify replacing the existing stable control.

---

## D-V8-067 — Define V8-A2 as a separate challenger branch

Date: `2026-09-01`

Decision:

All future movement-model improvements are developed as `V8-A2` challengers against frozen V8-A.

Reason:

A working control must not be contaminated by exploratory model, target or calibration changes.

---

## D-V8-068 — Retain explicit barrier-difficulty / regime representation as positive A2 research evidence

Date: `2026-09-01`

Decision:

Retain the 33 direction-free barrier-difficulty/regime features as a valid A2 research representation.

Reason:

Adding them to the original 53 features improved AUC over the frozen control in all 9 year/horizon cells for 2024/2025/2026 x 15/30/60m.

This is not promotion authority because Brier/calibration did not improve uniformly.

---

## D-V8-069 — Retain strict multi-horizon survival as the primary A2 challenger formulation

Date: `2026-09-01`

Decision:

Retain a unified first-hit-time target:

```text
class 0 = +/-10 hit <=15m
class 1 = hit during 15-30m
class 2 = hit during 30-60m
class 3 = no hit by 60m
```

with outputs:

```text
P15 = P(class0)
P30 = P(class0 or class1)
P60 = P(class0 or class1 or class2)
```

The research model uses original 53 + regime 33 features and regularized multinomial logistic modeling.

Reason:

The strictly rebuilt survival challenger beat frozen V8-A AUC in all 9 outer year/horizon cells, while preserving the natural monotonic relation P15 <= P30 <= P60.

It remains research-only.

---

## D-V8-070 — Multi-horizon survival labels require full 60-minute purge

Date: `2026-09-01`

Decision:

For any model whose target encodes information through 60 minutes, a training row is eligible only if:

```text
decision_time + 60m <= evaluation_boundary
```

regardless of whether P15, P30 or P60 is being evaluated.

Reason:

An audit found that an early exploratory A2 survival/stack run used output-horizon-specific purging. That could expose 30/60m class information across a 15m/30m evaluation boundary. Those exploratory stack/selective outputs are not authority. Strict survival results and the retained model manifest were regenerated with the full 60m purge.

---

## D-V8-071 — Do not use internal CV >=0.90 as promotion evidence

Date: `2026-09-01`

Decision:

A blocked-CV AUC above 0.90 does not authorize a V8-A2 model or justify a 90% accuracy claim.

Reason:

Some pre-2024 chronological folds exceeded 0.90 AUC, while the actual next-year 2024 outer performance remained near 0.86. Primary evidence remains past-to-future outer evaluation and later prospective shadow data.

Random K-fold is not authority.

---

## D-V8-072 — Define any 90% V8-A claim as selective and coverage-aware

Date: `2026-09-01`

Decision:

Do not optimize or advertise raw classification accuracy as the 90% objective.

Any 90% claim must include:

```text
precision or selective accuracy
coverage
calendar-year/regime breakdown
base movement rate
future-block stability
```

Reason:

The +/-10 movement base rate changed by an order of magnitude between 2024 and 2026, making raw accuracy highly misleading.

---

## D-V8-073 — Reject current nonlinear, excursion and tick branches as default A2 upgrades

Date: `2026-09-01`

Decision:

Do not prioritize shallow HGB, future-excursion distribution modeling or signless tick-feature accumulation as default V8-A2 improvement paths.

Reason:

They failed to produce stable incremental future-year improvement over the long-history M1 control. Tick-vs-M1 movement-label parity was 100% on aligned events, so the negative tick result was not explained by label mismatch.

---

## D-V8-074 — Treat online adaptation as calibration research, not automatic authority

Date: `2026-09-01`

Decision:

Monthly expanding/trailing refit and 180-day recalibration may be studied as controlled A2 calibration methods, but automatic live retraining is not authorized.

Reason:

Later-regime Brier scores improved modestly, but AUC did not jump materially and 2024 ranking could degrade. Reacting to short-term weakness can create online overfit.

---

## D-V8-075 — Prospective reliability monitoring precedes A2 promotion

Date: `2026-09-01`

Decision:

Before considering any V8-A replacement, prospectively log every supported decision with P15/P30/P60 and resolved outcomes, then monitor:

```text
AUC
Brier score
calibration by score bucket
decile hit-rate ordering
recent 30/60/90-day stability
```

Reason:

Current evidence suggests live risk is more likely to appear first as calibration/base-rate drift than as an immediate collapse of all movement ranking skill.

---

## D-V8-076 — Keep GOLD# 2021 locked after A2 tournament

Date: `2026-09-01`

Decision:

Do not spend GOLD# 2021 on the current A2 challenger.

Reason:

No A2 model passes the promotion gate. The reserve should remain untouched until an architecture is fully frozen and merits final temporal validation.
