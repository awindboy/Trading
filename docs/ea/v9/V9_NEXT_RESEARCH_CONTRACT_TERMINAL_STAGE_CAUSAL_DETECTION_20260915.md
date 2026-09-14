# V9 Next Research Contract — Terminal-Stage Causal Detection and HA Arming

Date: `2026-09-15`
Status: `ACTIVE SHADOW STRATEGY-RESEARCH CONTRACT`
Production authority: `NONE`
Strategy authority change: `NONE`
Market: `GOLD# ONLY`

## 1. Objective

The last-Child Heikin-Ashi oracle showed that exit quality may improve substantially if HA is activated only after terminal participation has been reached.

The oracle is non-causal. The next research objective is therefore:

> Estimate `TERMINAL_STAGE` using only information causally known at the time, arm frozen H4 HA logic only after that estimate, and measure the full sequential economic result against the current BASE role policy.

The project is **not** trying to predict the exact final top/bottom or the literal future last Child with certainty.

The practical question is:

```text
Has the route matured enough that the next opposite H4 HA should be treated as a route-level profit-protection event rather than an ordinary mid-journey pullback?
```

## 2. Frozen baseline

Do not change these mechanics during this contract:

- H1/H4 causal 2-left / 2-right liquidity;
- tick-native H4 Arrival chronology as execution authority;
- PRIMARY_ACTIVE / CHALLENGED Grammar;
- nearest active opposite H1 structural SL;
- previous-completed H4 Wilder ATR180 ERA scale;
- `ERA_RISK <= 4` entry eligibility;
- ANCHOR / CONTINUATION role definition;
- BASE Anchor `CHALLENGE_OPENS` exit;
- BASE Continuation `NEXT_H4_LIQ` exit;
- no fixed TP, SHORT ban, session/day/hour/duration filter, or Child-count cap.

BASE remains the comparator, not something to repair in-place.

## 3. Frozen HA challengers

The first study must keep the HA definitions fixed:

```text
HA1 = first completed opposite-color H4 Heikin-Ashi after arming
HA2 = second consecutive completed opposite-color H4 Heikin-Ashi after arming
```

At the HA event:

- first primary challenger: close every still-open Child in that route;
- Anchor-only close remains a control;
- existing structural/base exit wins if it happens first;
- H4 close is a research reference only until actual-tick execution is studied.

Do not add wick/body thresholds, zero-wick rules, HA strength scores, or other fitted HA variants in the first causal study.

## 4. Oracle target

For labeling only, the consumed answer sheet may define:

```text
LAST_ACCEPTED_CHILD = the final accepted Child in that route before the route resolves
```

This label can be used to study terminal-stage discrimination.

It must never appear as an input feature and must never be used to arm HA in the causal replay.

Secondary labels may include:

- whether another accepted Child is earned before challenge;
- number of future accepted Children (diagnostic only);
- future additional primary MFE / ATR180;
- future giveback to BASE exit / ATR180;
- `PROTECT_NOW` as an outcome diagnostic.

No future label may leak into causal features.

## 5. Decision points

Primary decision point:

```text
immediately after each accepted Child / eligible same-side H4 Arrival
```

At that point the detector may output a continuous terminal-stage score.

The score itself does not exit.
It only decides whether HA monitoring is armed.

Once armed in a replay, the arming state must be frozen/persisted according to the preregistered policy; do not use later outcomes to disarm/repair the route unless a causal disarm rule is independently preregistered.

## 6. Candidate causal feature families

### A. H4 liquidity geometry — primary family

- nearest remaining same-side H4 liquidity distance / ATR180;
- second/third same-side distances / ATR180;
- nearest opposite H4 liquidity distance / ATR180;
- same/opposite distance ratio;
- SAME_NEAREST / OPPOSITE_NEAREST as descriptive topology;
- active same/opposite H4 liquidity counts;
- active liquidity age summaries;
- current consumed H4 liquidity age;
- gaps/missing same-side target state.

Earlier shadow research indicates that H4 liquidity geometry can outperform high-dimensional raw H1 chart features for journey-end classification. Treat that as motivation, not a frozen threshold.

### B. Journey realization

Continuous variables only unless semantically categorical:

- route age;
- elapsed time since Anchor;
- accepted-Child rank/count as a raw descriptor only;
- cumulative primary-direction expansion / ATR180;
- Anchor current PnL / ATR180;
- Anchor MFE / ATR180;
- Anchor giveback / ATR180;
- active Continuation state;
- realized results of already closed Continuations.

Do not convert count/age into hand-picked thresholds after seeing the answer sheet.

### C. HTF movement capacity

Use completed H1/H4 only:

- directionless movement-capacity score(s);
- route-relative change from Anchor entry;
- change from previous accepted Child;
- ATR14 / ATR180 activity ratio;
- multi-window range/volatility/efficiency summaries.

### D. H1 chart state

Keep low-dimensional and causal:

- 3/6/12/24/48h range / ATR180;
- realized volatility;
- directional efficiency;
- body/range and overlap summaries;
- current location within recent H1 range.

Do not reintroduce broad indicator mining unless a simpler baseline fails and a preregistered reason exists.

## 7. Required model ladder

Evaluate in this order:

1. **single-variable mechanical rankings** — especially H4 same-side distance;
2. **small mechanical score / monotonic combination**;
3. logistic regression;
4. shallow decision tree;
5. nonlinear model only if it adds stable walk-forward information.

The study must explicitly answer:

> Does ML beat the same causal variables used mechanically?

Complexity is not a success criterion.

## 8. Validation design

All supplied history is consumed. Therefore no result is untouched OOS.

Use strict chronological development evidence:

```text
pre-2024 -> 2024
pre-2025 -> 2025
pre-2026 -> 2026
```

Where a threshold/arming rate is required, select it using prior-period data only. Do not choose a 2026 threshold from 2026 outcomes.

Use route-cluster uncertainty where practical because multiple checkpoints belong to the same journey.

Report direction and year slices, but do not create side-specific rules from postmortem differences.

## 9. Sequential policy test — primary acceptance gate

Checkpoint AUC is secondary.

For each causal detector candidate:

```text
route begins
-> BASE entries/SL mechanics unchanged
-> detector evaluated only at causal decision points
-> detector may arm HA according to frozen rule
-> once HA event occurs, close according to frozen HA policy
-> no future repair/revival
-> continue chronological replay
```

Primary outputs:

- total fixed-size gross PnL;
- PF;
- WR;
- max drawdown;
- year-by-year PnL/PF;
- UP/DOWN diagnostics;
- Anchor/Continuation contribution;
- single/multi-Child journey contribution;
- P90/P95/max winner and right-tail capture;
- number and timing of armed routes;
- number of false early arms;
- amount of BASE right-tail lost to false early activation;
- fraction of oracle improvement recovered.

A candidate that improves AUC but cuts the right tail and lowers sequential economics fails.

## 10. Mechanical-vs-ML comparison

The same feature availability and same decision timestamps must be used.

Do not give ML extra hindsight context unavailable to the mechanical comparator.

Compare at matched intervention/arming rates when possible, in addition to each method's preregistered operating point.

The question is not `which model is smarter?`.
It is:

> Does nonlinear combination provide stable incremental decision value beyond simple interpretable H4 liquidity geometry?

## 11. Prohibited fitting

Do not promote or search exhaustively for:

- `3rd Child`, `4th Child`, or any Child-count threshold;
- fixed elapsed-time terminal rule;
- fixed MFE terminal rule;
- fixed GOLD-distance threshold;
- direction-specific terminal thresholds;
- SHORT-only HA;
- mandatory HA1 because the oracle HA1 was best;
- HA candle body/wick micro-rules;
- retry/cooldown/trade quotas.

The oracle is a target for understanding activation timing, not permission to reverse-engineer its answer with thresholds.

## 12. Falsification conditions

Downgrade the terminal-stage program if any of the following persist after clean causal testing:

- terminal discrimination collapses toward chance walk-forward;
- good classification does not improve sequential economics;
- gains come mainly from one year or one direction;
- improvements require fitted Child-count/time thresholds;
- false early arms materially destroy 4+ Child right-tail journeys;
- simple mechanical features perform as well as or better than ML and no stable incremental information appears;
- estimated improvements disappear after actual-tick Bid/Ask execution.

A negative result is acceptable. Do not repair it with additional filters.

## 13. Promotion gate

No strategy authority changes during this contract.

A future promotion proposal requires, at minimum:

1. causal walk-forward shadow result;
2. clear mechanical semantics of the arming state;
3. robustness across years and both directions without fitted exceptions;
4. retained large-winner capture;
5. actual-tick execution replay for HA close events;
6. forward-demo logging before live-capital authority.

Until then:

```text
BASE prototype exits remain authority.
TERMINAL_STAGE and HA are shadow fields only.
```

## 14. Relationship to forward-demo contract

`V9_NEXT_RESEARCH_CONTRACT_FORWARD_DEMO_20260914.md` remains valid for the frozen BASE prototype.

The execution lane and terminal-stage research lane may proceed separately, but terminal-stage shadow findings must not silently alter the EA R1 BASE semantics used for forward-demo comparison.
