# V8 Research State

Status: `ACTIVE / ATR GRID DIRECTION-ERROR ABSORBER / SIZING + WRONG-DIRECTION ACTION NEXT`
Date: `2026-09-04`
Production authority: `NONE`
Market: `GOLD# ONLY`
Untouched reserve: `GOLD# 2021`
Source Git HEAD at synchronization: `bbe30f7d23d13def712ad53117df9e8bc42a5e2e`

## 1. Stable upstream conclusions

### P15

`fresh75` remains a valid near-term movement/excursion opportunity state.

P0 fresh75:

- 2024 653
- 2025 535
- 2026 321
- total 1509

Fresh75 to actual `+/-0.25S` touch within 15m remains about `77.8%`.

P15 does not provide robust initial direction.

### ACCEPTANCE

P0 ACCEPTANCE:

- 279 / 236 / 153
- total 668

P2 ACCEPTANCE:

- 316 / 235 / 144
- total 695

ACCEPTANCE is a structural transition, not a finished direction/entry rule.

### Structural retention

`micro3` remains an initial structural-quality prior.

Dynamic state remains:

    PRISTINE
    DAMAGED
    CLOSE_BROKEN

No structural label is an automatic trading action.

### Winner continuation

High-Q remains sparse but economically positive development evidence.

P0:

- N61
- mean about +0.287R
- PF about 1.68-1.71

P2:

- N70
- mean about +0.214R
- PF about 1.53-1.56

## 2. Closed or downgraded direction branches

Current evidence does not justify reopening these without a new mechanism:

- generic fresh75 direction classifier;
- reveal FOLLOW / FADE;
- every-M1 LONG/SHORT EV;
- rolling EV retraining;
- direct probability sizing;
- micro first-touch direction;
- simultaneous LONG+SHORT synthetic straddle;
- simple stop-and-reverse;
- continuous M1 trend-follow;
- random-direction payoff search.

The repeated lesson is:

> Movement onset is much easier than robust initial direction.

## 3. Coverage lesson

A delayed t10 state was profitable but sparse:

- P0 N126 total
- WR 59.5%
- mean +0.197R
- PF 1.57

This is only about 8.35% of all P0 fresh75 events.

It is preserved as state evidence, not final strategy architecture.

Research must report full campaign coverage and never hide denominator collapse.

## 4. ATR-grid branch

The active idea is to use ATR-scaled staged exposure as a `direction-error absorber`.

Intended economic outcomes:

- correct initial direction -> protected directional winner;
- wrong initial direction but normal rotation -> weighted-BE rescue;
- wrong initial direction that becomes genuine opposite continuation -> reduce / exit / flip before the large tail;
- continuation after base economics are secured -> possible separate runner/add tranche.

Current focused scaffold:

- weak causal initial direction: 30m momentum hypothesis;
- entries around `0`, `-0.4S`, `-0.8S`;
- hard adverse control around `-1.2S`;
- `+1S` is a progress/protection milestone;
- protected runner target around `+1.5S`;
- weighted BE is rescue;
- no mandatory fixed timeout.

These values are research scaffolding, not production parameters.

## 5. M1 versus tick authority

M1 is allowed for:

- broad family screening;
- geometry;
- state characterization;
- hazard research.

Exact tick is mandatory for:

- multi-fill chronology;
- weighted-BE chronology;
- Bid/Ask execution;
- candidate profitability.

M1 favorable intrabar assumptions previously generated false positive grid results.

## 6. Causal-alignment guardrail

For a `15:35` decision whose origin is the `15:34` close:

- legal feature data ends at 15:34;
- execution begins at 15:35.

A 1-minute look-ahead was found and all affected results were discarded.

Every future study must declare `known_at` for each feature.

## 7. Current payoff state

The user rejected `+1S` as final TP.

The revised structure uses:

- `+1S` = progress milestone;
- protected runner toward about `+1.5S`.

Representative P0 2024 exact-tick improvement:

Old +1S exit:

- mean about +$0.248/campaign
- average winner about +$12.15

Revised protected +1.5S:

- mean about +$0.378/campaign
- average winner about +$18.65

P2 2024 exact tick remained approximately flat:

- mean about -$0.015/campaign
- PF about 0.996

Therefore the economics improved but are not yet robust enough.

## 8. BE interpretation

Weighted-BE touch is a rescue event.

It is not reliable proof that the original direction has restarted.

Do not leave the full grid basket running after BE without independent continuation evidence.

Same-direction High-Q inside a live campaign is interesting development evidence for a separate continuation tranche, but simply moving the existing TP farther to +3S worsened economics.

## 9. Current main bottleneck

The large remaining problem is not normal BE recovery.

It is the deep adverse tail.

For the current equal-size three-tranche scaffold:

- hard losses concentrate after the third tranche / roughly `-0.8S`;
- P0 deep-state N about 153;
- P2 deep-state N about 180;
- BE recovery and hard loss split about 52% / 48%.

Among eventual hard-loss cases, roughly 78-80% later deliver an opposite-direction `+1.5S` diagnostic move.

This suggests the high-value problem is:

> Detect genuine opposite continuation after the deep-adverse state and convert some hard losses into smaller losses or opposite-direction winners.

## 10. Campaign RR problem

Equal size `1:1:1` at `0`, `-0.4S`, `-0.8S` with hard boundary `-1.2S` has basket loss `2.4S`.

Direct first-unit target is about `+1.5S`.

Gross campaign RR:

    1.5 / 2.4 = 0.625

The loss side is too large.

Tightening the price stop harmed recovery.

The next approach is to preserve price room while changing size and actions.

## 11. Immediate next research

Compare identical geometry with:

Fixed:

    1 : 1 : 1

Decreasing:

    1 : 0.5 : 0.25
    1 : 0.5 : 0.5
    1 : 0.25 : 0.25

Martingale:

    1 : 2 : 4

Then combine with deep-state actions:

    HOLD
    REDUCE
    EXIT
    FLIP

Report actual dollars, exposure and tail losses.

## 12. Sequential validation

- 2024 -> development/training.
- 2025 -> exact-tick validation using only 2024 knowledge.
- 2026 -> retrain through 2025, then validate.

The user stated that 2025 GOLD tick data has been uploaded. The next session must verify the file and use it.

## 13. Production status

`NONE`

No sizing or wrong-direction rule is frozen.
