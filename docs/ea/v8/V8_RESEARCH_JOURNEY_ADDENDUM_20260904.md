# V8 Research Journey Addendum — 2026-09-04

Status: `SESSION HISTORY / FAILURE AND COURSE-CORRECTION RECORD`
Production authority: `NONE`

This document records the reasoning path of the 2026-09-04 research session so future sessions do not repeat the same failed loops.

## 1. Starting point

The project entered this session with:

- reliable movement-onset evidence from P15;
- weak initial direction;
- structural-retention models;
- a sparse but positive High-Q continuation component;
- a negative routine ACCEPTANCE Base.

The active problem was how to turn the supported modules into a broad executable strategy without collapsing trade count.

## 2. First hypothesis — every-M1 EV instead of fixed checkpoints

The user challenged fixed t3/t5/t10 checkpoints.

The idea was:

> If reveal/ACCEPTANCE/t10 are not truly directional, evaluate LONG/SHORT/WAIT every M1 instead of waiting for arbitrary confirmations.

This was the correct falsification to perform.

Result:

- direct every-M1 direction EV remained unstable;
- some 2024-H2 linear results were weakly positive;
- nonlinear variants failed;
- month-to-month relation reversed;
- P(win) x payoff was essentially flat.

Lesson:

> Replacing a classifier with EV notation does not manufacture missing direction information.

## 3. Delayed t10 candidate and trade-count objection

A t10 state did show positive economics.

But the user noticed the repeated structural problem:

    1509 fresh75
    -> 668 ACCEPTANCE
    -> 254 unresolved
    -> 126 favorable unresolved

The candidate was profitable because it selected a narrow state.

The user correctly rejected treating it as a full solution.

Lesson:

> Every candidate must be judged simultaneously on economics and coverage.

## 4. Attempt to remove direction prediction through micro first-touch

A new idea was to let the market choose direction through the first tiny barrier touch.

M1 looked promising.

Exact tick showed:

- BuyStop/Ask and SellStop/Bid create asymmetry;
- after symmetric direction observation, the edge disappeared.

Lesson:

> Direction observation coordinates and execution coordinates must be separated.

## 5. Attempt to buy direction uncertainty

Several structures attempted to avoid direction prediction entirely:

- simultaneous LONG+SHORT;
- synthetic straddle with independent SL/TP;
- stop-and-reverse;
- continuous trend-follow.

All failed after real execution costs and whipsaw.

Lesson:

> Direction uncertainty is not free. Spread and path reversal can be the price of buying information.

## 6. Shift to ATR interval trading

The user proposed the old V7 KTR-style idea:

> If direction is imperfect, use intervals to improve average price and escape on rotation.

This was the first major conceptual shift.

The key new question became:

> Can the strategy absorb ordinary direction error and only lose on true one-way continuation?

## 7. First major research mistake — micro-grid slicing

The initial implementation incorrectly compressed the idea into:

- 0.08S / 0.20S spacing;
- many small fills;
- tiny BE+alpha exits.

This produced high M1 WR but weak economics.

The user correctly objected that the supposed interval trade was just slicing an M1 candle.

Lesson:

> Preserve the scale and economic meaning of the user hypothesis before optimizing parameters.

## 8. Spread misunderstanding

When M1 positivity disappeared under exact tick, the first explanation overemphasized spread.

Actual-dollar decomposition showed:

- the normal win was tiny;
- the hard loss was much larger;
- zero-spread same-path was already near breakeven.

The corrected conclusion was:

> The edge was thin before spread; spread was not the sole cause.

Lesson:

> Always show actual dollars and same-path zero-spread control before attributing failure to broker cost.

## 9. Second major research mistake — overexpanding the horizon

After the user objected to the micro-grid, the research swung too far:

- 0.5-1.5S spacing;
- 3h to 24h holding.

This improved BE recovery mechanically but changed the strategy into a multi-hour mean-reversion system.

The user correctly pointed out that P15 is a near-term movement model.

Lesson:

> Do not correct one scale error by creating the opposite scale error.

## 10. Return to the original economic objective

The user clarified the intended payoff:

- if direction is right -> take a meaningful TP;
- if direction is wrong -> use the grid to escape around BE;
- if the wrong-direction move becomes a genuine one-way trend -> cut or flip;
- if oscillation fills extra entries and the original direction later works -> the extra entries should ideally increase profit.

This became the correct architecture.

## 11. Third major research error — 1-minute look-ahead

A timestamp audit found:

- decision 15:35;
- origin = 15:34 close;
- execution legally begins 15:35.

An intermediate momentum implementation accidentally included the 15:35 M1 and started execution at 15:36.

All affected results were discarded.

Lesson:

> Every research table needs explicit feature cutoff and execution start.

## 12. Economic reporting correction

The user challenged reports focused on:

- spacing;
- legs;
- AUC;
- horizon.

The correct report must instead answer:

- What was the initial direction accuracy?
- How many direct TPs?
- How much did a TP earn in dollars?
- How many wrong directions were rescued to BE?
- How much did hard losses lose?
- What did an intervention reduce?
- What was the total economic effect?

This is now mandatory.

## 13. The +1S TP problem

The user then identified a deeper payoff flaw.

If the strategy's large loss is much larger than the +1S winner, then calling +1S "direction success" is economically weak.

The research changed:

    +1S = progress/protection
    +1.5S = protected winner reference

This increased average winner meaningfully in 2024 P0 tick.

Lesson:

> A probability architecture can still fail if the payoff definition is economically wrong.

## 14. Grid winner amplification hypothesis

The user expected multiple grid fills to amplify profit if the original direction later truly resumed.

A direct attempt to leave the full basket running after BE failed.

Many baskets touched BE and then immediately fell back.

Lesson:

> BE recovery is not continuation confirmation.

Possible next role for High-Q:

- secure the rescue/base first;
- if continuation evidence then add a separate runner tranche.

## 15. Timeout challenge

Large timeout counts raised another conceptual problem.

Holding former timeouts longer showed:

- many later TPs;
- many later BE rescues;
- a smaller number of very large one-way losses.

So neither fixed timeout nor unlimited waiting is a complete answer.

Lesson:

> Time should be a hazard feature unless a clock exit is independently justified.

## 16. Venn-diagram reframing

The user proposed the clearest current conceptual model:

    TP
    BE
    SL

TP:

- initial direction is correct and sustained.

BE:

- initial direction is wrong/noisy but rotation rescues.

SL:

- initial direction is wrong and becomes real opposite continuation.

This shifted the highest-value research target away from squeezing more winner profit.

The central question became:

> Can SL trades be identified early enough to convert a large loss into a smaller loss or opposite winner?

## 17. Deep-adverse branchpoint discovery

Hard losses concentrated after the third staged fill / around -0.8S.

At that state the population was close to:

- half BE recovery;
- half hard loss.

Simple entry-time direction features were weak.

After the deep state, path separation began to appear.

Lesson:

> The direction problem may not be learnable at fresh75, but the rotation-vs-one-way problem may become learnable after sufficient adverse evidence.

## 18. Reward/risk correction

A second important economic correction:

Three equal tranches with a -1.2S boundary do not risk 1.2S.

They risk:

    1.2 + 0.8 + 0.4 = 2.4S

Against a +1.5S first-unit winner, gross RR is only 0.625.

Tightening the price stop damaged recovery.

Therefore:

> Preserve price room, change exposure.

## 19. New sizing direction

The user asked to compare:

- fixed;
- decreasing;
- martingale.

The martingale branch is especially interesting because it can move weighted BE aggressively toward the most recent fill.

But it can also explode tail risk.

This is where the session ended.

## 20. Immediate next-session research

Do not continue parameter wandering.

Start from the current focused geometry and compare sizing schedules.

Then use 2024 exact tick for development and 2025 exact tick for validation.

At the deep adverse state compare:

    HOLD
    REDUCE
    EXIT
    FLIP

The first success criterion is not AUC.

It is:

> actual dollar improvement in the hard-loss population without destroying the BE-recovery population.

## 21. Errors that must never be repeated

- shrinking the denominator until a pretty result appears;
- confusing model target semantics;
- micro-grid scale drift;
- multi-hour scale drift;
- M1 intrabar optimism;
- spread scapegoating;
- missing dollar decomposition;
- missing basket-exposure RR;
- treating +1S as automatically enough;
- treating BE as continuation;
- using future labels causally;
- timestamp look-ahead;
- keeping a stale 2024-only model through 2026;
- turning censored gaps into outcomes.
