# V8 ATR Grid Direction-Error Absorber Research

Date: `2026-09-04`
Status: `DEVELOPMENT / PARTIALLY EXACT-TICK VALIDATED / NOT PRODUCTION`
Market: `GOLD# ONLY`
Untouched reserve: `GOLD# 2021`
Source Git HEAD: `bbe30f7d23d13def712ad53117df9e8bc42a5e2e`

## 1. Research question

The original V8 sequence had a persistent bottleneck:

    movement onset was predictable
    initial direction was not

Repeated attempts to wait for reveal, ACCEPTANCE or other confirmations often reduced trade count without creating a broad direction edge.

The ATR-grid branch asks a different question:

> Can we tolerate a weak initial direction, absorb ordinary adverse rotation with staged ATR entries, escape wrong/noisy direction at weighted BE, and reserve predictive effort for the smaller set of genuine opposite one-way continuations?

This is inspired by the old V7 KTR interval-trading concept but is not a direct copy.

The V8 distance coordinate is `S`, the previous-completed H4 Wilder ATR14.

## 2. Pre-grid direction research that motivated the branch

### Every-M1 direct EV

Removing t3/t5/t10 checkpoints and recalculating direction every M1 did not solve direction.

Representative fixed-validation results:

- 2025 selected N307, WR 48.2%, mean -0.036R
- 2026 selected N297, WR 48.5%, mean -0.030R

A 2024-H1 trained linear action-value model on 2024-H2:

- validation campaigns 314
- entered 271
- WR 47.2%
- mean +0.068R
- PF 1.145

But monthly reversal was material, including October about -0.141R, and nonlinear models failed.

A P(win) x payoff version:

- N298 / 314
- WR 44.3%
- mean about -0.001R
- PF about 0.997

Interpretation:

> EV did not create missing directional information.

### Delayed t10 state

A profitable delayed state existed:

- ACCEPTANCE virtual Base unresolved at t10;
- accepted-direction MTM > 0;
- enter +0.75S / -0.40S runner.

P0 total:

- N126
- WR 59.5%
- mean +0.197R
- PF 1.57

P2 total:

- N133
- WR 56.4%
- mean +0.146R
- PF 1.38

But 126 is only about 8.35% of all P0 fresh75.

This state is not the final high-frequency strategy.

### Exact tick micro first-touch

M1 suggested a micro first-touch edge.

Exact tick removed it after correcting Bid/Ask asymmetry.

Representative corrected result:

- `+/-0.05S`, `+0.50S/-0.40S`, 30m
- N624
- WR about 45.2%
- mean about -0.054R

Direction-free straddles, stop-and-reverse and continuous trend structures also failed.

## 3. Original ATR-grid hypothesis

The user articulated two benefits.

### Direction-error absorption

If the initial direction is wrong but price does not become a full one-way trend, staged entries improve weighted average and can allow a BE exit on rotation.

### Pre-move accumulation

If the initial direction is ultimately right but price oscillates before departure, additional favorable-price fills can potentially increase the eventual winner payoff.

The main risk is the small number of true one-way opposite moves.

Existing V8 states might be useful not as direction gates but as:

- add reduction;
- add stop;
- early cut;
- opposite flip;
- continuation add.

## 4. First implementation error: micro-grid

Early exploratory spacings included:

- 0.08S;
- 0.20S;
- tiny BE+alpha exits.

For 2024 median S about $11.8:

- 0.08S about $0.94 GOLD;
- 0.20S about $2.36.

This was too close to M1 noise.

A representative M1 `0.08S x5 / BE+0.05S` structure had apparent WR around 96%.

Exact tick changed the result to roughly:

- P0 WR 86.2%;
- mean -0.0366R.

Actual-dollar anatomy was approximately:

- average success +$1.11;
- average hard loss -$14.44;
- worst about -$26.35.

The strategy was not a strong edge destroyed by spread.

A same-path zero-spread replay was roughly breakeven.

Lesson:

> Tiny repeated rescue profits plus rare large losses are not the intended V8 interval architecture.

## 5. Why M1 was misleading

Grid execution can change state multiple times inside one M1.

Example:

- adverse grid level is touched;
- new weighted BE becomes valid;
- the same M1 high/low also contains that BE.

OHLC does not reveal whether:

    add -> BE

or:

    old high -> add

occurred.

Therefore M1 can be used for structural screening but not final grid execution P/L.

## 6. Second implementation drift: too-long horizon

The next exploration moved to:

- 0.5-1.5S spacing;
- 3h / 4h / 8h / 24h.

This produced high BE recovery but drifted away from the original V8 event.

The user correctly pointed out that P15 concerns near-term movement.

The grid is intended to complement that event, not create a separate all-day mean-reversion system.

This multi-hour branch is not current authority.

## 7. Causal timing correction

During the corrected near-term research a 1-minute look-ahead was discovered.

If the V8 event decision is at 15:35 and origin is the 15:34 close:

Legal:

    features <= 15:34
    execution >= 15:35

Invalid intermediate code allowed the 15:35 M1 into momentum and executed from 15:36.

All affected results were discarded.

## 8. Return to the intended payoff

The user objected that a grid strategy should not merely produce many tiny profits.

The intended economic decomposition became:

### Correct initial direction

Do not stop at a trivial small TP.

A meaningful directional move should produce a meaningful winner.

### Wrong/noisy initial direction

Use staged fills to improve weighted average.

If normal rotation returns to BE, escape.

### Wrong initial direction + genuine opposite trend

This is the dangerous SL population.

The strategy should identify and reduce/exit/flip these cases.

## 9. Why +1S was reclassified

A +1S move is meaningful, but not necessarily the end of a directional winner.

The prior +1S immediate exit generated representative P0 2024 exact-tick economics:

- mean +$0.248/campaign
- total +$154.25
- average winner +$12.15
- average loser -$14.43
- PF about 1.106

Revised architecture:

    +1S = protection/progress milestone
    protected target around +1.5S

P0 2024 exact tick:

- completed 622
- mean +$0.378/campaign
- total +$235.37
- average winner +$18.65
- average loser -$18.07
- PF about 1.110

P2 2024 exact tick:

- mean about -$0.015/campaign
- PF about 0.996

The right-tail correction helped, but robustness remains insufficient.

## 10. Representative M1 screening across years

Corrected M1 screening showed the protected-runner change improved the problematic 2025 branch.

Representative mean dollars/campaign:

### P0

Old +1S exit:

- 2024 +0.249
- 2025 -0.438
- 2026 +4.941

Protected +1.5S:

- 2024 +0.400
- 2025 +0.158
- 2026 +4.857

### P2

Old +1S:

- 2024 +0.075
- 2025 -0.673
- 2026 +5.097

Protected +1.5S:

- 2024 +0.177
- 2025 +0.093
- 2026 +5.587

These are M1 screening results, not execution authority.

## 11. BE recovery did not imply runner continuation

A natural hypothesis was:

> If several grid tranches filled and price returns to weighted BE, keep the basket open because the original direction may finally be starting.

Exact tick showed this was unreliable.

Many recovered baskets immediately moved back through BE.

Therefore:

- weighted BE is the default rescue objective;
- full-basket continuation after BE is not currently supported;
- new continuation must be treated as a separate action.

## 12. High-Q inside a live campaign

Small development evidence:

P0 same-direction High-Q:

- N21
- average +$16.81
- 18 runner TP
- 0 hard loss

P2:

- N25
- average +$17.13
- 0 hard loss

But moving the existing High-Q target from +1.5S to +3S worsened the result.

This suggests:

> secure the base/rescue economics first, then consider a separate High-Q continuation tranche rather than moving the whole basket TP.

No rule is frozen.

## 13. Fixed timeout investigation

A 45/60m forced timeout produced a very large timeout population.

When former timeouts were followed longer, most eventually resolved favorably or at BE, but a minority became large hard losses.

Representative former-timeout decomposition:

- about 31% later direct TP;
- about 58% later BE;
- about 11% hard loss.

The hard-loss magnitude was enough to worsen total expectancy.

Conclusion:

- fixed clock exit is too crude;
- infinite holding is also unsafe;
- elapsed time is state information, not necessarily an action by itself.

## 14. TP / BE / SL Venn-style decomposition

The current research is best understood as three economic populations.

### TP

The initial direction is correct and price sustains it.

### BE

The initial direction is wrong/noisy, but price rotates back enough for staged positions to escape.

### SL

The initial direction is wrong and the market continues in the opposite direction strongly enough to invalidate rescue.

The main research leverage lies in SL.

Turning a hard loss into an opposite winner has a much larger impact than adding a small amount to an already positive winner.

## 15. Current focused three-tranche scaffold

The latest focused geometry uses:

    initial entry       0
    second entry      -0.4S
    third entry       -0.8S
    hard boundary     -1.2S

Direction is currently a weak causal 30m momentum hypothesis for the scaffold.

Winner path:

    +1S progress/protection
    -> protected runner toward about +1.5S

Rescue path:

    weighted BE
    -> rescue complete unless separate continuation evidence exists

No fixed timeout is mandatory.

These are research values, not final parameters.

## 16. Hard-loss concentration

In 2024 exact tick, hard losses concentrated in campaigns that reached the third tranche / roughly -0.8S.

Representative deep-state population:

- P0 about 153;
- P2 about 180.

Approximate outcome from that state:

- BE recovery about 52.3%;
- hard loss about 47.7%.

This is a much better-defined decision problem than trying to predict direction at fresh75.

## 17. Why the hard-loss state may be learnable

At initial entry, simple features did not separate hard loss from recovery well.

Tested/inspected examples included:

- M15/M30/M60 alignment;
- first 30 seconds to 3 minutes;
- early adverse movement;
- time to first grid fill.

After reaching the deep adverse state, path behavior became more informative.

Illustrative diagnostics:

- after about 5m, still around/beyond -0.95S -> hard-loss rate in high-70% range;
- around/beyond -1.0S -> roughly 90% in a small cell;
- recovery toward -0.7S/-0.6S -> much lower hard-loss rate.

These thresholds are not frozen.

The next step is action-value mapping.

## 18. Hard losses often become opposite winners

Among current hard-loss events, a large majority later produced a substantial opposite-direction move.

Diagnostic only:

- P0 about 79.5% later produce opposite +1.5S first;
- P2 about 77.9%.

This supports the hypothesis that the hard-loss class is not random noise.

Many are genuine initial-direction errors.

The next research should ask whether causal information after -0.8S can identify enough of these to justify an opposite flip.

## 19. Basket reward/risk problem

The equal-size scaffold has a fundamental exposure asymmetry.

At the -1.2S boundary:

    first tranche loss  = 1.2S
    second tranche loss = 0.8S
    third tranche loss  = 0.4S
    total                = 2.4S

The first-unit protected winner target is about +1.5S.

Therefore gross campaign reward/risk is:

    1.5 / 2.4 = 0.625

The current loss side is too large.

## 20. Why simply tightening SL failed

A tighter adverse price boundary can reduce nominal basket loss, but it also eliminates many normal GOLD rotations that would otherwise recover to BE.

A trial around a -0.9S boundary worsened the economics.

Therefore the next principle is:

> Keep enough price room for normal rotation, but reduce the exposure that is added as evidence becomes more adverse.

## 21. Next sizing families

### Fixed

    1 : 1 : 1

### Decreasing

    1 : 0.5 : 0.25
    1 : 0.5 : 0.5
    1 : 0.25 : 0.25

For `1 : 0.25 : 0.25`, current -1.2S boundary risk is:

    1.2*1 + 0.8*0.25 + 0.4*0.25
    = 1.5S

This creates a gross 1:1 reference against the +1.5S initial-unit target without tightening the price boundary.

### Martingale

    1 : 2 : 4

Martingale will pull the weighted BE sharply toward the latest entry.

That may create more profitable deep recoveries.

But it also creates very large tail exposure.

It must be evaluated with:

- hard-loss average and worst dollars;
- notional exposure;
- margin;
- tail contribution;
- drawdown potential.

## 22. Next exact-tick validation

The user states 2025 GOLD tick data is now available.

The next study must validate the current branch on 2025 exact ticks.

2024 remains development/training.

2025 must be independent validation.

If a model is later tested in 2026, retrain with 2024+2025.

## 23. Required next action table

At the third-fill / deep adverse state, construct the causal action table:

    HOLD
    REDUCE
    EXIT
    FLIP

For each state/action report:

- N;
- average dollars;
- total dollars;
- PF if applicable;
- downstream TP / BE / SL mix;
- worst loss;
- tail contribution.

AUC is secondary.

The primary question is whether the action improves actual campaign economics while preserving normal BE recovery.

## 24. Current conclusion

The ATR-grid idea remains alive, but only in a narrower and more disciplined form.

Supported:

- staged exposure can rescue many initial-direction errors;
- hard losses are concentrated in a more specific deep-adverse state;
- many hard losses appear to be genuine opposite-direction moves;
- winner payoff improves when +1S is treated as progress rather than final TP.

Not yet supported:

- current equal-size basket RR;
- current P2 2024 execution edge;
- a causal wrong-direction flip rule;
- martingale safety;
- a final spacing/leg count;
- production use.

Immediate priority:

> sizing comparison + 2025 exact-tick validation + deep-state HOLD/REDUCE/EXIT/FLIP economics.
