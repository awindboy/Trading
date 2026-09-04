# V8 Decisions Addendum — Grid Sizing and Deep Action

Date: `2026-09-04`  
Status: `ACTIVE RESEARCH DECISIONS`  
Production authority: `NONE`

## Decision 1 — Use reproducible P0 2024 N=648 for this execution stage

The prior synchronized count `653` and the now-reproducible old P0 count `648` are not silently merged.

The user explicitly authorized this exact-execution stage to proceed with the reproducible `648` population after clarifying how `653` had been promoted in the prior session.

This is a documented population-version correction, not permission to rewrite unrelated historical counts without rebuilding them.

## Decision 2 — 2025 exact tick is unavailable

The uploaded 2025 tick package is incomplete/sparse. Treat it as absent for full-year exact execution validation.

Do not claim 2025 exact-tick OOS validation. M1 remains descriptive only. GOLD# 2021 remains locked.

## Decision 3 — Static decreasing sizing does not solve the grid

Under the same -1.2S boundary, all preregistered decreasing schedules underperformed fixed because their farther weighted BE caused too many lost rescues.

Do not promote `1:0.5:0.25`, `1:0.5:0.5`, or `1:0.25:0.25` as standalone fixes.

## Decision 4 — Martingale 1:2:4 is rejected for this geometry

It increased BE rescue frequency but created excessive tail exposure and worse total economics.

Do not add more martingale depth or tune the sequence to rescue this branch.

## Decision 5 — Equal-risk wider boundaries are not promoted

Outcome-blind equal-risk boundaries were checked after the primary same-geometry test. Pairwise complete-event economics still favored fixed and wider boundaries risk reopening multi-hour mean-reversion drift.

Do not interpret raw positive means from schedule-specific completed populations as edge; censoring was materially schedule-dependent.

## Decision 6 — Deep-state hard-loss probability is not the action target

At -0.8S and even at -1.1S, EXIT can improve a majority of individual losing paths while still reducing mean dollar EV because sacrificed BE recoveries are larger.

All action research must target action-conditioned dollars, not classifier accuracy alone.

## Decision 7 — Unconditional deep-state REDUCE / EXIT / FLIP are rejected

On the common exact-tick deep-state population, HOLD had the highest future economic value.

Do not convert third fill itself into an automatic intervention trigger.

## Decision 8 — Five-minute action model is not promoted

An intermediate xmin/xmax implementation leaked future data and was invalidated immediately.

The corrected causal compact model showed only moderate discrimination and failed expanding-quarter action-value stability.

Do not reuse the invalid AUC or tune thresholds around the corrected model.

## Decision 9 — Simple adverse thresholds are rejected

Unconditional interventions at -0.9S, -1.0S and -1.1S all reduced mean dollar value versus HOLD.

Do not continue threshold rescue on this same action family.

## Decision 10 — Conditional one-unit hedge is downgraded

The -1.0S opposite one-unit hedge with -1.2S profit exit / -0.8S rebound exit had small positive ideal zero-spread value but negative actual Bid/Ask value.

This is a thin pre-cost edge, not a strong edge destroyed by spread.

Do not optimize hedge size/thresholds from the same 2024 outcomes.

## Decision 11 — Fixed 1:1:1 remains control, not strategy authority

Fixed sizing is the best tested static control for this stage, but its strict-gap +1S execution-control edge is approximately +$0.053/campaign with PF about 1.015.

This is too thin for production and the +1S control is not the final payoff objective.

## Decision 12 — Next branch must change payoff shape

Do not run another HOLD/EXIT threshold tournament.

Any next grid-related mechanism must be preregistered and must aim to preserve normal-rotation recovery value while creating stronger convex protection against genuine opposite continuation.

Same-path zero-cost and actual Bid/Ask economics are mandatory.
