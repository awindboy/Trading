# V8 Next Research Contract — P15-Centered Causal State-Transition & Persistence Audit

Date: `2026-09-05`  
Status: `PREREGISTERED NEXT PRIMARY RESEARCH`  
Production authority: `NONE`  
Market: `GOLD# ONLY`  
Untouched reserve: `GOLD# 2021`

## 1. Research question

Primary question:

> After P15 identifies a near-term movement disturbance/opportunity, can we causally identify a transition into a persistent market state whose direction, distance and lifetime are more stable and economically larger than generic next-bar direction signals?

This is NOT a generic direction classifier project.

It is NOT a copy of Mesfin's GMM/Markov thresholds.

It is NOT a new fixed t10 confirmation gate.

## 2. Why this branch is opened

Internal evidence:

- P15 is strong for near-term movement but weak for broad direction;
- static/current direction features repeatedly approach chance or fail after exact execution;
- Late Ignition, BB Persistence and Macro are all better described as processes/state changes than as static patterns;
- V3 showed that state x local event x acceptance can work in discovery but strict serial confirmation causes scarcity and can still fail validation;
- Directional Change is a stable price representation but did not add broad incremental direction information.

External supporting evidence:

- long-horizon time-series momentum suggests persistence can be more learnable than fresh reversal prediction;
- Mesfin (2026) provides a falsification example where many short-horizon OHLCV signals fail while separate positive controls are state/regime-transition oriented and operate on longer horizons;
- this evidence is hypothesis support only, not strategy authority.

## 3. Population authority

Use the currently reproducible P0/P0R event populations already built for V8:

- 2024: exact-execution development universe available;
- 2025: M1 descriptive/screening only; no exact-tick authority;
- 2026: M1 descriptive/screening only;
- 2021: untouched.

Do not silently merge P0/P2 or historical 648/653 variants.

## 4. Shadow-first non-interference rule

The first stage is **shadow-only**.

It must not alter:

- P15 authorization;
- Entry;
- SL;
- TP;
- sizing;
- scenario lifecycle;
- current module selection.

No trading gate is promoted until the state-transition hypothesis survives the glass-ceiling audit.

## 5. Event chronology

For each fresh75 event, define:

    t0 = causal fresh75 decision time

Pre-event descriptors may use only information known strictly before t0 according to existing V8 known-at rules.

Post-event descriptors at t0+5m, +10m, +15m, +30m, +60m, etc. are shadow observations only during the discovery audit.

A future observation may describe the path for research but may never be used as if it were known at t0.

If a later executable transition trigger is designed, its `known_at` timestamp must be explicit and execution can occur only after that timestamp.

## 6. Frozen descriptor families for the first audit

The first audit should use a small, semantically separated descriptor set rather than a large feature tournament.

### Activity / movement intensity

Examples:

- ATR-normalized recent true range;
- relative tick activity;
- short-window range expansion versus trailing baseline.

### Directional efficiency

Examples:

- absolute net displacement / traveled path;
- signed net displacement normalized by S;
- persistence of same-direction closes.

### Balance / overlap

Examples:

- bar overlap ratio;
- recent compression/expansion ratio;
- time or bar occupancy inside the prior local range.

### Value migration / acceptance

Use only causal chart-derived proxies at first:

- rolling price center/median movement;
- persistence outside prior balance/value proxy;
- reclaim/failure semantics.

Do not call broker tick volume true centralized volume profile.

### Higher state

Use existing V3/V8 higher-state descriptors only where semantics are already reproducible:

- M30/H1 ownership/delivery context;
- existing HTF movement state.

### Directional Change

Allowed only as shadow path coordinate.

Do not add DC alignment as a trading gate; its broad direction audit is already negative.

## 7. Two representations, neither with automatic trade authority

The first audit may use two complementary forms.

### A. Continuous transition geometry

Measure how descriptors change from pre-event to post-event states.

Examples:

    delta activity
    delta efficiency
    delta overlap
    delta value center

The goal is to find broad stable transition geometry, not a profitable threshold.

### B. Outcome-blind state partition

An unsupervised partition may be used as a descriptive tool only.

Requirements:

- choose a small natural state count before opening P/L;
- fit only on the allowed discovery segment;
- map states semantically using descriptor centroids, not arbitrary numeric labels;
- test whether semantics survive 2024 H1/H2 and later years;
- do not retune cluster count because one transition has better P/L.

GMM is not privileged. The outside paper's exact method is not copied.

## 8. Primary object: transition, not state

Do not ask only:

    state == X -> LONG?

Ask:

    state/process A
    -> P15 disturbance
    -> transition toward B
    -> does B persist?

Candidate transition families should be named by causal/market meaning, for example:

- balance -> initiative expansion;
- quiet -> ignition;
- expansion -> persistent delivery;
- expansion -> failed auction/reclaim;
- correction -> resumed delivery.

Names are descriptive hypotheses, not trading rules.

## 9. Persistence targets

Before any payoff optimization, quantify persistence on multiple natural horizons.

At minimum examine:

- short: ~15m;
- medium: ~30m;
- extended intraday: ~60m;
- optional ~90m only if state evidence remains alive.

For each transition family report:

- state persistence rate;
- signed displacement distribution;
- MFE/MAE normalized by S;
- first-touch direction at fixed natural barriers;
- continuation conditional on an initial +1R-equivalent survival checkpoint;
- failure/reclaim rate.

Do not choose the horizon by highest P/L.

## 10. Glass-ceiling audit requirements

Every candidate transition must be attacked before trade design.

### Coverage / scarcity

Report:

- source denominator;
- transition N;
- year split;
- monthly/quarterly concentration;
- overlap with existing modules.

If quality appears only after serially shrinking the population toward V3-like scarcity, treat that as failure unless it represents a genuinely independent high-payoff module.

### Chronological invariance

At minimum:

- 2024 H1 vs H2;
- 2025 M1 descriptive;
- 2026 M1 descriptive.

Do not repair a sign reversal by moving a threshold.

### Representation invariance

Check whether semantic meaning survives small natural choices in:

- trailing window length;
- descriptor scaling;
- state-count choice if unsupervised partition is used.

The exact best cell is not the target.

### Naive/mirror controls

Every directional transition must beat appropriate controls such as:

- simple prior momentum;
- plain breakout continuation;
- plain breakout fade;
- static state without transition;
- random/time-matched P15 controls where feasible.

### Incremental information

Measure whether a proposed transition is merely a restatement of:

- Late Ignition;
- BB Persistence + HTF;
- scheduled Macro;
- DC alignment;
- basic M5 owner transition.

Parameter variants do not count as orthogonal edges.

### Economic edge margin

Only after a transition relationship survives the above:

    structural gross edge
    - realistic friction/execution
    = edge margin

Do not call a thin pre-cost relationship a strong edge destroyed by spread.

## 11. Existing-module unification test

A specific mandatory diagnostic:

> Test whether Late Ignition, BB Persistence + HTF and Macro reactions occupy distinguishable transition paths in the common descriptor space.

Possible outcomes:

1. **Common transition mechanism**  
   They are manifestations of one broader process. Then unify semantics but do not double-count modules.

2. **Different transition mechanisms**  
   They remain orthogonal causes. Preserve portfolio separation.

3. **Representation-only overlap**  
   Descriptors look similar but outcomes/cause differ. Do not merge them merely because a cluster groups them.

Outcome-blind cause identity remains important.

## 12. Failed-auction lane inside this framework

Do not separately threshold-mine another failed-auction pattern first.

Within transition analysis, define failed auction semantically as:

    attempted expansion / probe
    -> inability to persist in new area
    -> reclaim toward prior value/balance
    -> opposite acceptance only if causally observed

Compare against simple breakout fade.

If this transition is genuinely independent and stable, it may become a new scenario module later.

## 13. Macro lane remains parallel and information-expanding

Do not wait for price-only research to finish before preparing macro data definitions.

Separate future contract:

    scheduled release
    -> pre-event state
    -> actual-consensus surprise when legally/causally known
    -> first reaction
    -> reaction acceptance/failure

Macro must remain explicitly separate from chart-only transition discovery because it expands the information set.

## 14. Promotion ladder

A candidate may progress only in this order:

    shadow transition relationship
    -> invariance / controls / incremental-information pass
    -> causal executable transition timestamp
    -> M1 payoff screening
    -> 2024 exact Bid/Ask execution development
    -> later independent execution validation when data exists

No stage may be skipped because a backtest looks attractive.

## 15. Stop rules

Stop or downgrade a branch if:

- it is only next-bar direction in new terminology;
- state labels reverse semantics across periods;
- it requires a cluster-count/threshold rescue after validation failure;
- population collapses without compensating payoff evidence;
- it is mostly one existing module under a new name;
- exact execution edge margin is negligible;
- the only improvement comes from extending TP/horizon without persistence evidence.

## 16. Success criteria for this research phase

The phase succeeds even without a tradable strategy if it produces one of these clear outcomes:

### Positive

A stable, interpretable transition family with:

- adequate population;
- persistent direction/distance relationship;
- invariance across time/natural perturbations;
- incremental information beyond current modules;
- plausible edge margin large enough to justify exact execution work.

### Negative

A well-supported conclusion that price-only post-P15 state transitions do not materially exceed current module information.

That negative result would justify moving more research weight toward information-expanding macro/order-flow lanes.

## 17. No production authority

`NONE`

No GOLD# 2021 use.
