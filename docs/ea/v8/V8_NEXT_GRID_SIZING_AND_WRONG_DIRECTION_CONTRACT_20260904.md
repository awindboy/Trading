# V8 Next Research Contract — Grid Sizing and Wrong-Direction Action

Date: `2026-09-04`
Status: `PREREGISTERED NEXT WORK`
Production authority: `NONE`
Market: `GOLD# ONLY`
Untouched reserve: `GOLD# 2021`

## 1. Purpose

The next research must answer two questions.

### Question A — sizing

Under the same ATR-grid geometry and the same initial direction hypothesis, how do fixed, decreasing and martingale tranche schedules change:

- weighted BE;
- BE recovery;
- direct winner payoff;
- hard-loss size;
- total expectancy;
- tail concentration;
- exposure/margin?

### Question B — wrong-direction action

After a campaign reaches the current deep-adverse state, can causal information choose:

    HOLD
    REDUCE
    EXIT
    FLIP

so that eventual hard losses are reduced or converted into opposite winners without sacrificing too many normal BE recoveries?

Do not open unrelated indicator families until these two questions are completed.

## 2. Data authority

### M1

Use current GOLD# M1 data for broad descriptive checks only.

M1 is not final execution authority for multi-fill grid economics.

### Exact tick

2024 exact tick:

- development;
- action/sizing construction;
- replay debugging.

2025 exact tick:

- independent validation.

The user states 2025 GOLD tick data is uploaded in project sources.

Before research, verify:

- exact file path;
- date range;
- timezone;
- timestamp precision;
- Bid/Ask schema;
- duplicates;
- missing intervals;
- month/file boundaries.

Any campaign crossing missing tick coverage is censored/incomplete.

## 3. Sequential-learning rule

For any learned hazard/action model:

### 2025 validation

    train = data available through 2024
    test  = 2025

### 2026 validation

    train = 2024 + 2025
    test  = 2026

Do not use 2025 labels to tune the 2025 rule.

Do not use 2026 labels to train 2026.

## 4. Current focused geometry

Use the current scaffold as the primary control first:

    initial entry       0
    second entry      -0.4S
    third entry       -0.8S
    adverse boundary  -1.2S

Direction:

- current weak causal 30m momentum hypothesis;
- it is not considered a strong direction model;
- keep it fixed while testing sizing so sizing comparisons are apples-to-apples.

Winner:

    +1S = progress/protection milestone
    protected objective around +1.5S

Rescue:

    weighted BE

No mandatory fixed timeout.

This geometry is a control scaffold, not a frozen final parameter set.

Do not optimize spacing during the first sizing comparison.

## 5. Sizing families

Normalize the first tranche to one unit for research.

### A. Fixed

    1 : 1 : 1

### B1. Decreasing

    1 : 0.5 : 0.25

### B2. Decreasing

    1 : 0.5 : 0.5

### B3. RR-reference decreasing

    1 : 0.25 : 0.25

At -1.2S, B3 basket loss is:

    1.2*1 + 0.8*0.25 + 0.4*0.25
    = 1.5S

This matches the initial-unit +1.5S winner target on a gross 1:1 basis.

### C. Martingale

    1 : 2 : 4

Do not add more martingale depth in the first test.

The purpose is to characterize the trade-off, not optimize a martingale sequence.

## 6. Required analytic calculations before replay

For every sizing schedule calculate analytically:

- total units after each fill;
- weighted average price in S coordinates after each fill;
- distance from latest price to weighted BE;
- basket loss at -1.2S;
- maximum notional units;
- direct first-unit +1.5S payoff;
- gross campaign reward/risk.

Example formulas:

For entries `e_i` and sizes `w_i`:

    weighted_BE = sum(w_i * e_i) / sum(w_i)

At adverse boundary `L`:

    basket_loss_S = sum(w_i * abs(L - e_i))

Report the actual dollar equivalent for 0.01-lot first-unit reference.

## 7. Required outcome categories

Every replay must classify each campaign into one final economic category.

### Direct/protected TP

Initial direction works without needing BE rescue.

Report:

- N
- percentage
- average $
- total $

### Grid recovery to BE

Initial path is adverse, staged entries fill, then weighted BE is recovered.

Report:

- N
- percentage
- average $
- total $

### Grid-before-winner

If the campaign becomes a winner after multiple fills under a separately defined continuation action, report separately.

Do not merge with direct TP.

### Early cut

A causal risk action exits before the control hard boundary.

Report:

- N
- average original control outcome $
- average early-cut outcome $
- average saved $
- total saved $

### Flip winner

A causal action reverses into the opposite direction.

Report:

- N
- original control outcome $
- flip outcome $
- incremental improvement $

### Hard loss

Report:

- N
- rate
- average $
- total $
- worst $
- fraction of all losses attributable to hard-loss tail

### Censored

Report N separately.

Do not include censored campaigns in win/loss rates unless explicitly using a separate mark-to-market analysis.

## 8. Required portfolio/campaign metrics

For every sizing schedule:

- total campaign N;
- completed N;
- censored N;
- mean $ / campaign;
- total $;
- PF;
- win rate under clearly defined win/flat/loss convention;
- average positive outcome $;
- average negative outcome $;
- max campaign loss $;
- 95th/99th percentile loss if sample permits;
- maximum units;
- average maximum units;
- hard-loss contribution to total negative P/L.

For martingale also report:

- maximum notional exposure relative to fixed;
- margin requirement proxy;
- worst consecutive hard-loss scenario;
- whether one hard loss can erase how many normal winners.

## 9. Deep-adverse state population

Primary state:

- third tranche filled;
- roughly -0.8S adverse progress.

Do not filter to survivors using future information.

At the moment the third fill becomes causally known, create the action-state dataset.

Potential causal features may include only information known by then or afterward at declared action times:

- elapsed time from fresh75;
- elapsed time between fills;
- latest progress in S;
- rebound from adverse extreme;
- recent 1/3/5m signed progress;
- path efficiency;
- local range/activity;
- current V8 structural state if causally available;
- adverse-direction reveal/ACCEPTANCE state if causally available;
- continuation/High-Q only if its required information time has actually occurred.

Do not use eventual BE, eventual hard loss or future opposite +1.5S as features.

## 10. Action definitions

### HOLD

Continue the control basket unchanged.

### REDUCE

Predefine exposure reductions, for example:

- close part of the latest tranche;
- close part of all tranches proportionally;
- stop adding while preserving existing basket.

Do not select the reduction type after viewing validation P/L.

### EXIT

Close the current basket at the action time.

### FLIP

Close the current initial-direction basket and enter opposite-direction exposure under a preregistered size/risk rule.

The flip rule must specify:

- entry price convention;
- lot size;
- stop;
- protection milestone;
- target;
- whether it may re-enter the original direction.

Keep the first flip experiment simple.

## 11. Model target

Do not optimize only:

    P(hard loss)

The economically relevant target is action-conditioned payoff.

Preferred analysis:

    Q(HOLD)
    Q(REDUCE)
    Q(EXIT)
    Q(FLIP)

where each Q is expected net dollars from the causal decision point onward.

A hard-loss classifier may be used as a diagnostic, but the final action must be justified by realized economic mapping.

## 12. 2024 discovery discipline

In 2024:

1. characterize each sizing schedule without a learned intervention;
2. identify the economic control;
3. build the deep-state action table;
4. fit only simple models first;
5. avoid large hyperparameter search;
6. freeze the candidate action before looking at 2025 outcome.

If multiple action rules are close, prefer the simpler rule and report all candidates considered.

## 13. 2025 validation discipline

Apply the frozen 2024-developed sizing/action rule to 2025 exact tick.

Required pass/fail report:

- full N;
- category decomposition;
- dollar economics;
- tail loss;
- sizing exposure;
- comparison with 2024;
- direction-specific and session/regime diagnostics only as descriptive secondary analysis.

Do not modify the rule to save 2025.

If 2025 reverses the relationship, record failure.

## 14. 2026 policy chronology

If the branch survives 2025:

- retrain/re-estimate the model with 2024+2025;
- freeze before 2026;
- test 2026.

This rule was explicitly requested by the user.

## 15. Primary hypotheses

### H1 — decreasing size

Decreasing size preserves price room while reducing basket tail loss.

Expected cost:

- weighted BE improves less aggressively;
- some rescues may be lost.

### H2 — martingale

Martingale moves weighted BE strongly toward the latest fill and may turn deep rebounds into positive exits.

Expected cost:

- hard-loss tail becomes much larger;
- margin and drawdown risk increase sharply.

Martingale passes only if the total economic tail remains acceptable.

### H3 — deep-state action is more learnable than fresh75 direction

The fresh75 direction problem has repeatedly failed.

The deep-adverse state already contains realized path information.

Hypothesis:

> normal rotation vs genuine opposite continuation is more separable after the third fill than direction is at fresh75.

### H4 — FLIP may have the highest leverage

Because about 78-80% of current hard-loss cases later show a substantial opposite-direction diagnostic move, a causal flip may convert some of the worst losers into winners.

This is a hypothesis only.

The future move cannot be used as a feature.

## 16. Failure conditions

Reject or downgrade a sizing/action rule if:

- positive expectancy comes only from one P0/P2 realization;
- 2025 exact tick reverses it;
- martingale tail dominates total expectancy;
- the rule requires unrealistic minimum-lot fractions without a scalable lot implementation;
- profit comes mainly from censored assumptions;
- trade coverage collapses;
- a threshold is a single-point optimum with no neighboring stability;
- actual spread/slippage destroys an already-thin zero-cost edge;
- M1 result fails exact tick;
- the action model has AUC but no positive dollar mapping.

## 17. Mandatory final report format

Start with the economic summary, not the model metric.

Example structure:

    Total campaigns: N
    Completed: N
    Censored: N

    Initial direction diagnostic:
      accuracy = X
      DIAGNOSTIC / NONCAUSAL if future-defined

    Direct/protected TP:
      N
      avg $
      total $

    BE rescue:
      N
      avg $
      total $

    Early cut:
      N
      control avg $
      intervention avg $
      total saved $

    Flip:
      N
      original avg $
      flipped avg $
      total improvement $

    Hard loss:
      N
      avg $
      worst $
      total $

    Net:
      mean $ / campaign
      total $
      PF
      max campaign loss
      exposure schedule

Then report model metrics.

## 18. Stop condition for the branch

If:

- fixed,
- decreasing,
- martingale,
- and deep-state HOLD/REDUCE/EXIT/FLIP

all fail meaningful 2025 exact-tick economics,

do not continue parameter rescue indefinitely.

Record that ATR-grid direction-error absorption did not solve the V8 directional bottleneck under the tested architecture and return to a genuinely new mechanism.

## 19. Production status

`NONE`

This contract defines the immediate next research only.
