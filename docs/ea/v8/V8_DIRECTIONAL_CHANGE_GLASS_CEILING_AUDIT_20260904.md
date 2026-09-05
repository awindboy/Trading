# V8 Directional Change — Glass-Ceiling Audit

Date: `2026-09-04`  
Status: `SHADOW AUDIT COMPLETE / BROAD DIRECTION USE REJECTED`  
Production authority: `NONE`  
Market: `GOLD# ONLY`  
Population: reproducible P0/P0R fresh75 research populations  
2024 exact execution: not required for broad rejection because no robust M1 directional relationship survived  
GOLD# 2021: `UNTOUCHED`

## 1. Purpose

Directional Change / intrinsic time was investigated under the new V8 glass-ceiling rules.

This was intentionally NOT a P/L threshold search.

The question was:

> Does Directional Change add stable conditional directional information beyond the existing V8 P15/scenario state, or is it mainly a robust re-expression of the same price history?

## 2. Pre-registered natural scales

No profitable threshold was searched.

Three natural H4-ATR-normalized scales were used:

    small  = 0.125S
    medium = 0.25S
    large  = 0.50S

where `S` is the event's previous-completed H4 Wilder ATR14 scale already used by V8.

For each fresh75 event, DC state was reconstructed causally from M1 closes strictly before the decision time.

Primary lookback:

    480 minutes

Natural initialization sensitivity was also checked at:

    240 / 480 / 960 minutes

No future bars were used for DC state assignment.

## 3. Primary target

Primary direction diagnostic:

    next +/-0.25S first-touch within 15 minutes

This matches the near-term P15 semantic scale.

Same-M1 both-touch cases are ambiguous and are not used as clean directional labels.

A secondary `+/-0.50S within 30m` diagnostic was also inspected to test longer-distance behavior.

No target was used to choose the DC thresholds.

## 4. Single-scale direction result

Directional continuation from the current DC state was approximately chance.

### Small 0.125S state -> next 0.25S/15m direction

- 2024: 50.69%
- 2025: 50.59%
- 2026: 50.78%
- 2024 H1: 46.43%
- 2024 H2: 54.86%

### Medium 0.25S state

- 2024: 51.38%
- 2025: 51.53%
- 2026: 48.63%
- 2024 H1: 47.62%
- 2024 H2: 55.08%

### Large 0.50S state

- 2024: 51.69%
- 2025: 53.70%
- 2026: 50.81%
- 2024 H1: 49.80%
- 2024 H2: 53.54%

Conclusion:

> A current DC direction at a natural scale is not a broad initial-direction edge for fresh75.

## 5. Multi-scale alignment — frequency versus quality

### Small + medium aligned

Population coverage:

- 2024: 79.2%
- 2025: 73.2%
- 2026: 76.3%

Clean next-0.25S direction accuracy:

- 2024: 51.32%
- 2025: 51.44%
- 2026: 49.49%

### Small + medium + large all aligned

Population coverage:

- 2024: 59.3%
- 2025: 55.7%
- 2026: 56.1%

Clean direction accuracy:

- 2024: 51.57%
- 2025: 53.65%
- 2026: 50.00%

2024 chronology:

- H1: 47.83%
- H2: 55.41%

This directly demonstrates the glass ceiling:

> requiring multi-scale agreement reduces the population materially without producing a stable directional edge.

The quality/frequency problem appears even though the DC representation itself is stable.

## 6. Incremental information outside existing scenario modules

The important test was not whether DC overlaps successful modules.

It was whether DC adds direction information to the much larger fresh75 population that is NOT already assigned to the current scenario families.

For 3-scale aligned events outside the existing current scenario-module population:

- 2024: 49.82%
- 2025: 54.21%
- 2026: 48.23%

2024:

- H1: 46.10%
- H2: 53.57%

Conclusion:

> DC alignment does not create a new broad orthogonal directional module outside the current scenario set.

This is the most important result of the audit.

## 7. Apparent positivity inside existing scenarios is not incremental proof

Three-scale DC alignment inside the already-selected current scenario population looked stronger in some cells, including 2024 and a very small 2026 cell.

But it was not stable across 2025 and module-level conditioning did not show a consistent incremental benefit.

For example, in endogenous late ignition, conditioning on DC alignment was:

- 2024: lower mean R than the full module;
- 2025: negative mean R while the full module stayed positive;
- 2026: stronger, but on small N.

Therefore do not add `DC alignment` as another gate to the current scenario portfolio.

## 8. Counter-scale / failed-overshoot-style state

A natural semantic state was also examined:

    medium and large DC agree
    while small DC points the opposite way

This is a candidate intrinsic-time correction / failed-small-overshoot state.

Following the small direction:

- 2024: ~45.1%
- 2025: ~46.7%
- 2026: ~53.2%

Following the large direction:

- 2024: ~54.9%
- 2025: ~53.3%
- 2026: ~46.8%

The relationship reverses in 2026.

Do not promote either continuation or reversal interpretation.

## 9. Overshoot-distance result

Fixed semantic bins of current DC overshoot progress were checked:

    <0.5 threshold
    0.5-1
    1-2
    >=2

No monotonic, time-stable continuation relationship survived across 2024/2025/2026.

Examples:

- large-scale `1-2` overshoot continuation was ~61% in 2024 but ~50% in 2025 and ~46% in 2026;
- large-scale `0.5-1` was weak in 2024 but much stronger in 2025;
- small/medium bins also changed meaning between 2024 H1/H2 and later years.

Therefore do not optimize an overshoot ratio threshold.

## 10. Longer-distance target

For the secondary `+/-0.50S within 30m` diagnostic, 3-scale alignment showed:

- 2024: ~57.9%
- 2025: ~57.9%
- 2026: ~49.5%

Outside existing scenario modules:

- 2024: ~56.5%
- 2025: ~57.9%
- 2026: ~48.4%

This fails the later-period stability requirement.

Do not convert it into a 0.50S directional strategy.

## 11. Lookback / initialization robustness

The DC representation itself is not fragile to the chosen causal initialization window.

3-scale alignment results at 240 / 480 / 960 minute lookbacks were nearly identical.

Event-state agreement versus the 480-minute reference was approximately:

- 240 vs 480: 99.7-100%;
- 960 vs 480: ~99.7-100%.

Direction accuracy was also effectively unchanged.

Interpretation:

> The broad failure is not explained by an arbitrary DC lookback initialization.

This strengthens the conclusion that the representation is stable but not incrementally directional.

## 12. Glass-ceiling classification

### Threshold sensitivity

No magical natural scale. Single-scale results are near chance.

### Frequency collapse

Requiring 3-scale alignment reduces fresh75 coverage to roughly 56-59% without stable quality gain.

### Overshoot-distance decay / instability

No monotonic stable overshoot threshold.

### Chronological stability

Failed. 2024 H1/H2 and 2026 materially change interpretation.

### Execution-cost sensitivity

Not escalated to a new exact-tick strategy because the broad M1 directional relationship itself is not sufficiently robust.

### Incremental information

Failed as a broad new module outside current scenario families.

### Representation stability

Passed. The DC state itself is reproducible across natural lookback windows.

## 13. Decision

`DIRECTIONAL CHANGE AS BROAD DIRECTION GATE = REJECTED / DOWNGRADED`

Directional Change may remain available as:

- a descriptive intrinsic-time coordinate;
- a semantic tool inside a genuinely independent scenario;
- a scale-normalized path representation for future research.

It must NOT be used as:

- a generic direction permission;
- a new filter added to current modules;
- a threshold tournament;
- evidence that intrinsic time alone solves V8 direction.

## 14. Research lesson

This audit directly supports the new permanent principle:

> A stable and elegant transformation of price history can still contain almost no new directional information.

The correct next question is not `Which DC threshold is best?`.

It is:

> Which genuinely different causal information or market process can resolve the scenario meaning that price-only DC state cannot?

## 15. Next research routing

Recommended next branches:

1. genuine failed-auction / rejection state using auction semantics, with naive mirror/breakout controls and no serial filter mining;
2. scheduled macro as an information-expanding lane, especially actual-consensus surprise plus post-release acceptance;
3. session-auction transitions only if they form an independent module rather than a time-of-day veto;
4. external COMEX/order-flow acquisition only when used to resolve scenario meaning rather than create an ultra-short generic signal;
5. keep DC as shadow context only unless a new causal interaction is preregistered.

No 2021 use.
