# V8 Development Handoff

Last updated: `2026-09-04`
Current phase: `GOLD P15 MOVEMENT -> ATR GRID DIRECTION-ERROR ABSORBER -> WRONG-DIRECTION / SIZING RESEARCH`
Production authority: `NONE`
Market: `GOLD# ONLY`
Open development evidence: `2022-2026`
Untouched reserve: `GOLD# 2021`
Source Git HEAD verified before this synchronization: `bbe30f7d23d13def712ad53117df9e8bc42a5e2e`

## 1. Immediate instruction to the next session

GitHub remains the project authority.

On resume:

1. refresh Git HEAD;
2. read `AGENTS_V8.md`;
3. read this file;
4. read `RESEARCH_STATE_V8.md`;
5. read `V8_ATR_GRID_DIRECTION_ERROR_ABSORBER_RESEARCH_20260904.md`;
6. read `DECISIONS_V8_ATR_GRID_ADDENDUM_20260904.md`;
7. execute `V8_NEXT_GRID_SIZING_AND_WRONG_DIRECTION_CONTRACT_20260904.md`.

Do not reopen old P0/P2 count archaeology, old direction-indicator tournaments, or old ACCEPTANCE threshold work unless a new direct contradiction changes the current conclusion.

The immediate next research is:

> For the current ATR-grid direction-error absorber, compare fixed, decreasing and martingale tranche sizing on exact 2024 and 2025 tick data, then test whether the deep-adverse state can causally choose HOLD / REDUCE / EXIT / FLIP without destroying normal BE recovery.

The user explicitly requested the first sizing families:

- fixed: `1 : 1 : 1`;
- decreasing, including at least `1 : 0.5 : 0.25`, `1 : 0.5 : 0.5`, `1 : 0.25 : 0.25`;
- martingale: `1 : 2 : 4`.

2025 exact-tick validation is mandatory if the uploaded 2025 GOLD tick files are available.

For model chronology:

- 2025 validation may use training through 2024 only;
- 2026 validation must retrain through 2025, i.e. use 2024+2025;
- never keep a 2024-only trained model frozen through 2026 merely for convenience;
- never leak validation-year information.

## 2. Hard scope

The user has frozen the research universe.

- GOLD# only.
- Do not research USDJPY#, XAUEUR#, BTCUSD# or another market.
- Do not reopen market-universe screening.
- Do not touch GOLD# 2021.
- P0 and P2 remain separate deterministic robustness realizations, not independent trades to merge.

## 3. Preserved upstream authority

The ATR-grid research does not erase the already-supported V8 layers.

### P15 / movement onset

Current P0 fresh75 authority:

- 2024: 653
- 2025: 535
- 2026: 321
- total: 1509

Fresh75 to actual `+/-0.25S` touch within 15m remains about `77.8%`.

Interpretation:

- P15 is a near-term movement/excursion opportunity signal;
- P15 is not a terminal direction signal;
- P15 should not be silently reinterpreted as a multi-hour trend forecast.

### ACCEPTANCE / structural quality

Current P0 ACCEPTANCE:

- 2024: 279
- 2025: 236
- 2026: 153
- total: 668

P2 ACCEPTANCE robustness:

- 2024: 316
- 2025: 235
- 2026: 144
- total: 695

ACCEPTANCE remains a structural state transition, not proven direct direction permission.

`micro3` remains an initial structural-retention quality prior.

Dynamic structural state remains:

    PRISTINE
    DAMAGED
    CLOSE_BROKEN

These labels must not automatically be converted into entry or exit rules.

### High-Q continuation

The strongest preserved executable component remains the sparse High-Q runner evidence.

P0:

- N61
- WR about 49.18%
- mean about +0.287R
- PF about 1.68-1.71
- average winner about +1.4R

P2:

- N70
- WR about 51.4%
- mean about +0.214R
- PF about 1.53-1.56

High-Q is better treated as continuation information after price has demonstrated strength, not as the initial direction gate for all fresh75 events.

## 4. Why the research moved away from ACCEPTANCE-gated entry

The central repeated failure was not movement detection.

The bottleneck was initial direction.

Repeated tests showed:

- fresh75 direct LONG/SHORT action EV was unstable or negative out of sample;
- reveal FOLLOW/FADE did not create stable direction economics;
- every-M1 direction EV did not create robust direction edge;
- rolling retraining did not fix the problem;
- probability sizing did not manufacture an edge;
- micro first-touch direction disappeared under exact tick implementation;
- synthetic bilateral straddles and stop-and-reverse structures failed after spread and whipsaw.

Therefore the current problem is not:

> How can we wait longer until direction becomes obvious?

Waiting through reveal / ACCEPTANCE / fixed t10 states repeatedly reduced population without creating a broad stable direction edge.

The current alternative is:

> Let P15 authorize a movement campaign, tolerate some initial direction error with ATR-scaled staged positioning, rescue normal rotation at weighted BE, and focus predictive effort on the smaller set of genuine opposite one-way continuations.

## 5. Important t10 result that must not be misused

A profitable downstream state was found after ACCEPTANCE:

- virtual Base unresolved at t10;
- accepted-direction MTM > 0;
- enter runner `+0.75S / -0.40S`.

P0:

- 2024: N44, WR 52.3%, mean +0.111R, PF 1.29
- 2025: N46, WR 60.9%, mean +0.159R, PF 1.45
- 2026: N36, WR 66.7%, mean +0.350R, PF 2.21
- total: N126, WR 59.5%, mean +0.197R, PF 1.57

P2 total:

- N133
- WR 56.4%
- mean +0.146R
- PF 1.38

This is preserved only as evidence that one particular delayed state has positive continuation EV.

It is not the final strategy because `126 / 1509` fresh75 events is only about `8.35%` coverage.

The user explicitly rejected this repeated pattern of obtaining nice P/L by shrinking the denominator.

## 6. Every-M1 EV research: conclusion

The user asked to remove fixed t3/t5/t10 checkpoints and calculate every M1.

The broad result was negative.

Representative fresh75 direct action-value policy:

- 2025 selected N307, WR 48.2%, mean about -0.036R;
- 2026 selected N297, WR 48.5%, mean about -0.030R.

A 2024-H1 trained linear every-M1 EV policy applied to 2024-H2 entered 271 / 314 campaigns:

- WR 47.2%
- mean +0.068R
- PF 1.145

but the monthly result reversed, including October about -0.141R, and nonlinear models failed.

A direct `P(win) x payoff` implementation was essentially flat:

- N298 / 314
- WR 44.3%
- mean about -0.001R
- PF about 0.997

Conclusion:

> Continuous EV reframing does not create directional information that is not present in the causal state.

Preserve EV as an action-evaluation framework, not as proof of direction edge.

## 7. Exact-tick falsification of micro first-touch

An M1-level micro first-touch candidate initially appeared positive.

Exact tick exposed two problems.

First, implementation asymmetry:

- BuyStop triggers through Ask;
- SellStop triggers through Bid;
- using the same origin directly therefore creates mechanical directional bias.

The corrected implementation observed direction on a symmetric Bid reference and used Bid/Ask only for execution.

After correction the edge disappeared.

Representative exact-tick 2024 results:

- `+/-0.05S`, TP `+0.50S`, SL `-0.40S`, 30m: N624, WR about 45.2%, mean about -0.054R;
- `+/-0.025S`, TP `+0.50S`, SL `-0.40S`, 60m: approximately breakeven, about +0.0003R.

Conclusion:

> M1 micro first-touch positivity was not a validated directional edge.

## 8. Direction-free structures that failed

The following were tested and are not current candidates:

- simultaneous LONG+SHORT locked hedge;
- synthetic straddle with independent small SL / large TP;
- simple stop-and-reverse;
- direction-free convex payoff searches;
- continuous M1 trend-follow / reversal structures.

Synthetic straddle search tested about 72 structural combinations and found no robust positive H1/H2 family; the least-negative region remained about -0.051 campaign-R.

Do not revisit these by threshold tweaking without a genuinely new mechanism.

## 9. ATR-grid research: why it was opened

The user proposed adapting the old V7 KTR interval-trading concept to V8's ATR coordinate.

The intended economic idea is:

- P15 says a near-term movement opportunity is likely;
- the initial direction may still be weak;
- staged entries absorb ordinary initial adverse rotation;
- if the initial direction was wrong but price rotates, the basket can escape around weighted BE;
- if the initial direction was ultimately correct after pre-move oscillation, the extra fills should improve average price and potentially amplify winner P/L;
- if the market becomes a genuine opposite one-way continuation, continuing to average is dangerous and should be reduced, stopped or flipped.

This is not a martingale thesis by default.

The research question is whether staged exposure plus causal hazard control can transform the initial-direction problem into a more learnable `normal rotation vs genuine opposite continuation` problem.

## 10. Research drift that must not recur: micro-grid slicing

The first ATR-grid implementation was too small.

Examples included:

- spacing `0.08S`;
- spacing `0.20S`;
- up to five legs;
- tiny `BE + 0.025S` or `BE + 0.05S` basket exits.

For 2024 median `S` around $11.8:

- `0.08S` is only about $0.94 GOLD;
- `0.20S` is about $2.36;
- median spread was about $0.22.

This was effectively slicing M1 noise, not the intended interval-trading architecture.

A representative `0.08S x 5 / BE+0.05S` M1 result showed roughly 96% WR, but 2024 exact tick fell to about:

- WR 86.2%
- mean -0.0366R

Representative actual-dollar anatomy:

- average successful campaign about +$1.11;
- average hard loss about -$14.44;
- worst around -$26.35.

A same-path zero-spread replay was roughly breakeven.

Therefore the correct conclusion is:

> Spread did not destroy a strong edge. The edge margin was already too thin, and execution friction plus intrabar ordering pushed it negative.

Never again report "spread killed the strategy" without a same-path zero-spread control and actual-dollar decomposition.

## 11. Research drift that must not recur: multi-hour overexpansion

The research then overcorrected into:

- spacing around 0.5-1.5S;
- 3h / 4h / 8h / 24h holding.

This created a separate multi-hour mean-reversion strategy and drifted away from P15's near-term semantics.

The user explicitly corrected this.

P15 is fundamentally a near-term movement opportunity model, roughly associated with the next 15m to about 1h.

Do not silently use P15 as a multi-hour trend predictor.

The current grid is intended to complement the existing V8 time scale, not replace it.

## 12. M1 versus tick: permanent execution rule

Grid strategies are unusually sensitive to intrabar ordering.

A single M1 may touch:

- a new adverse add level; and
- the new weighted-BE exit level.

OHLC cannot tell which came first.

Favorable ordering can make a grid positive; pessimistic ordering can make it negative.

Therefore:

- use M1 for broad geometry, state and family screening;
- use exact tick for candidate execution economics;
- use actual Bid/Ask;
- mark tick gaps as censored/incomplete;
- never infer a win/loss across missing tick coverage.

## 13. Critical causal-timing error that must never recur

A 1-minute look-ahead was discovered during this session.

For a decision stamped `15:35`, the V8 origin was the `15:34` M1 close.

Correct causal alignment:

    features may use data through 15:34
    decision occurs at 15:35
    execution can begin at 15:35

An intermediate implementation accidentally began execution at 15:36 and included the 15:35 M1 in the momentum feature.

All affected results were discarded and recomputed.

Permanent guardrail:

> For every feature, write down the exact last legal timestamp before evaluating P/L.

## 14. Economic reporting correction

The user explicitly rejected reports that emphasized only:

- grid spacing;
- number of legs;
- AUC;
- holding horizon.

Every future grid report must show the actual economic anatomy.

Minimum required fields:

- total fresh75 campaigns;
- completed / censored;
- initial-direction diagnostic accuracy, clearly marked noncausal if based on future first-touch;
- direct/protected TP count;
- direct/protected TP average and total dollars;
- grid-before-winner count and dollars if applicable;
- weighted-BE rescue count;
- BE rescue average and total dollars;
- early-cut count, original expected loss and actual loss after intervention;
- flip count and opposite-direction winner dollars;
- hard-loss count, average dollars, total dollars and worst case;
- mean dollars per campaign;
- total dollars;
- PF;
- maximum campaign loss;
- tail contribution;
- lot/exposure schedule.

AUC must never be presented as an executable result by itself.

## 15. Current payoff correction: +1S is not final directional success

The user correctly challenged the use of `+1S` as a final TP.

`S` is the previous-completed H4 ATR14 coordinate.

A move of `+1S` is meaningful progress, but it is not automatically the end of a successful directional campaign.

The research therefore changed:

- `+1S` = progress / protection milestone;
- the protected runner target was extended to around `+1.5S`.

Representative 2024 exact-tick P0 comparison:

Old `+1S` immediate exit:

- completed about 622
- mean +$0.248 / campaign
- total +$154.25
- PF about 1.106
- average winner +$12.15
- average loser -$14.43

Revised `+1S -> protected +1.5S runner`:

- completed 622
- mean +$0.378 / campaign
- total +$235.37
- PF about 1.110
- average winner +$18.65
- average loser -$18.07

P2 2024 exact tick was still approximately breakeven:

- mean about -$0.015 / campaign
- PF about 0.996

Conclusion:

> Extending the right tail improved the economic shape, but the candidate remains too thin for promotion.

## 16. BE is rescue, not continuation confirmation

Exact tick showed that simply reaching weighted BE after a deep grid excursion does not mean the original direction has restarted.

When all grid tranches were left open after BE, many campaigns immediately fell back through BE.

Therefore:

- default weighted-BE touch means the rescue objective has been achieved;
- do not automatically promote the whole grid basket into a runner;
- continuation requires independent evidence.

Same-direction High-Q inside a live campaign produced encouraging but small development evidence:

P0:

- N21
- average about +$16.81
- 18 direct runner TPs
- 0 hard losses

P2:

- N25
- average about +$17.13
- 0 hard losses

However, simply extending High-Q targets from +1.5S to +3S worsened P/L.

Interpretation:

> High-Q may support a separate additional continuation tranche after base economics are secured, not an unconditional farther TP for the existing basket.

## 17. Fixed timeout is not the strategy

Large timeout counts appeared under 45m/60m forced exits.

When former 45m timeouts were held longer:

- many later reached TP;
- many later recovered to BE;
- a smaller group became large hard losses.

Representative former-timeout decomposition was roughly:

- about 31% later direct TP;
- about 58% later BE recovery;
- about 11% hard loss.

Therefore:

- a fixed 45m/60m clock exit is too crude;
- unlimited waiting is also dangerous;
- elapsed time may be a hazard feature;
- exit should be primarily price/state driven;
- right-censored campaigns remain incomplete.

## 18. Current TP / BE / SL interpretation

The user proposed a useful conceptual decomposition.

- TP: initial direction is correct and sustained.
- BE: initial direction is wrong or noisy, but rotation rescues the staged basket.
- SL: the initial direction is wrong and price develops into a genuine opposite one-way continuation.

The central value of future research is not merely squeezing more profit from existing winners.

If an eventual SL campaign can be recognized early and flipped:

- one large loss may disappear;
- the same event may become an opposite-direction winner.

That can improve expectancy far more than increasing TP by a small amount.

## 19. Current focused scaffold

The current focused research scaffold is not production authority.

Representative geometry:

- initial direction: weak causal 30m momentum hypothesis;
- staged entries in the initial direction:
  - level 1 at 0;
  - level 2 around `-0.4S`;
  - level 3 around `-0.8S`;
- hard adverse boundary control around `-1.2S`;
- `+1S` = progress/protection milestone;
- protected runner objective around `+1.5S`;
- weighted BE = rescue level;
- no mandatory fixed timeout.

Do not freeze `0.4S` as a final production spacing.

It is the current focused test scaffold.

## 20. Deep-adverse branchpoint

2024 exact-tick research showed hard losses were concentrated after the third tranche / roughly `-0.8S` adverse state.

Representative population:

- P0 deep-state N about 153;
- P2 deep-state N about 180.

After reaching this state, the split was approximately:

- BE recovery: about 52.3%;
- hard loss: about 47.7%.

This is the main current decision point.

Diagnostic future labeling also showed that among hard-loss campaigns:

- P0 roughly 79.5% later delivered an opposite-direction +1.5S move first;
- P2 roughly 77.9%.

This future information is diagnostic only and must never be used as a causal feature.

Simple information at initial entry did not clearly identify these trades:

- M15/M30/M60 alignment;
- first 30 seconds to 3 minutes;
- initial adverse progress;
- first-grid fill speed.

Separation became more visible only after the deep adverse state.

Illustrative, non-frozen diagnostics after the third fill:

- still near or beyond about `-0.95S` after roughly 5m -> hard-loss rate in the high-70% range;
- around `-1.0S` -> about 90% hard loss in a small diagnostic cell;
- recovery toward `-0.7S` or `-0.6S` -> substantially lower hard-loss risk.

Do not freeze these thresholds.

The next research must evaluate HOLD / REDUCE / EXIT / FLIP in dollars.

## 21. Campaign RR correction

Equal-size entries at:

- 0;
- `-0.4S`;
- `-0.8S`;

with hard boundary `-1.2S` produce basket loss:

    first tranche  = 1.2S
    second tranche = 0.8S
    third tranche  = 0.4S
    total          = 2.4S

A direct first-unit winner to `+1.5S` earns only `1.5S`.

Therefore the gross campaign reward/risk is:

    1.5 / 2.4 = 0.625

The apparent first-entry price-distance ratio is misleading.

Campaign RR must include all tranche exposure.

Tightening the price stop to about `-0.9S` to force a nominal 1:1 basket RR damaged normal recovery and worsened the economics.

The current hypothesis is therefore:

> Preserve enough price room for GOLD rotation, but reduce or reshape exposure as adverse evidence accumulates.

## 22. Immediate next sizing research

The next session must compare the same geometry and same direction/exits under multiple size schedules.

### Fixed

    1 : 1 : 1

### Decreasing

At minimum:

    1 : 0.5 : 0.25
    1 : 0.5 : 0.5
    1 : 0.25 : 0.25

The `1 : 0.25 : 0.25` schedule is an important reference.

At a `-1.2S` boundary the basket loss is:

    1.2*1 + 0.8*0.25 + 0.4*0.25
    = 1.5S

This matches the first-unit `+1.5S` winner target on a gross 1:1 basis while preserving the same price room.

### Martingale

    1 : 2 : 4

The user explicitly wants this tested because the weighted BE moves much faster toward the latest entry and a deep rebound may become profitable well before the equal-size BE.

But the martingale branch must report:

- maximum basket loss;
- maximum notional exposure;
- tail contribution;
- margin implications;
- hard-loss frequency;
- average and worst hard-loss dollars.

A high BE-recovery rate is not sufficient if the tail loss becomes catastrophic.

## 23. 2025 exact tick is now part of the next validation

The user stated that 2025 GOLD tick data has been uploaded to the project sources.

This session ended before the file could be fully inspected.

The next session must first:

1. refresh GitHub HEAD;
2. locate the exact 2025 tick file or files;
3. verify time range;
4. verify timezone;
5. verify Bid/Ask schema;
6. verify timestamp resolution;
7. check duplicates and month-boundary gaps;
8. fail closed on missing coverage;
9. reuse the same exact-tick replay conventions as 2024.

Validation chronology:

- 2024: development / training;
- 2025: independent exact-tick validation using only knowledge through 2024;
- 2026 M1 or later exact-tick validation: retrain with 2024+2025 before testing 2026.

## 24. Next-session decision problem

At the deep adverse state, compare:

    HOLD
    REDUCE
    EXIT
    FLIP

For each action compute actual campaign-dollar outcome, not only a classifier score.

The primary target is:

> Convert as many future hard-loss campaigns as possible into smaller losses or opposite-direction winners while preserving as much as possible of the normal BE-recovery population.

This is the most important active V8 question.

## 25. Permanent research errors that must not recur

1. Do not shrink denominator through repeated confirmation gates and then present the small profitable subset as a broad solution.
2. Do not use P15 outside its supported time semantics without a new validation.
3. Do not confuse M1 OHLC ordering with executable tick chronology.
4. Do not blame spread without zero-spread same-path control.
5. Do not hide actual dollars behind R when the user needs economic scale.
6. Do not report AUC without an action and economic mapping.
7. Do not treat BE recovery as proof of continuation.
8. Do not treat `+1S` as automatically final TP.
9. Do not judge campaign RR from first-entry TP/SL distance while ignoring added exposure.
10. Do not use future outcome labels as causal decision features.
11. Do not reintroduce the 1-minute causal-alignment look-ahead.
12. Do not freeze a threshold because one year or one realization looked good.
13. Do not train 2026 policy on 2024 only when 2025 is legally available.
14. Do not classify censored tick gaps as wins or losses.
15. Do not merge P0 and P2 as independent trading samples.

## 26. Production status

Production authority remains:

`NONE`

The current ATR-grid work is a research branch intended to solve the direction-error problem while preserving the validated P15 movement opportunity and continuation evidence.

No EA change should be promoted until:

- exact-tick economics are positive and meaningful;
- fixed/decreasing/martingale sizing are compared;
- 2025 exact-tick validation survives;
- tail loss is economically acceptable;
- direction-error handling is causal;
- cost-adjusted expectancy and drawdown are acceptable;
- 2021 remains untouched until preregistered final validation.
