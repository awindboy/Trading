# V12 Phase-1I run-episode reverse-engineering contract

Date frozen: `2026-09-24`

Status: `CONSUMED-DEVELOPMENT REVERSE ENGINEERING / NO TRADE OR SIZING AUTHORITY`

Contract: `v12-phase1i-run-episode-reverse-engineering-v1`

## Why this phase exists

Phase 1H still treated each Child as the main prediction unit. That can improve
individual stop discrimination without answering the actual decision: is the
market entering another alternating-loss run, or is a tail-producing journey
beginning?

Phase 1I reverses the unit of analysis. It first labels completed FAST runs by
their realized economic role, then returns to the first actual-entry decision
of each run and asks what was already causally observable.

Raw profit is not the primary objective. The primary objective is removing a
material share of repeated stopped units while retaining frequent journey
participation. A result that removes little stopped exposure while deleting
large tail capital fails by contract.

## Frozen episode vocabulary

One observation is one funded FAST-HA run at its first actual-entry decision.

- `TAIL_JOURNEY_RUN`: the run later produces at least one `>=5R` right-tail
  unit;
- `STOP_ONLY_RUN`: the run has stopped units and no `>=5R` right tail;
- `NEUTRAL_RUN`: every other funded run.

The primary avoidable repeat is a `STOP_ONLY_RUN` immediately following the
previous funded `STOP_ONLY_RUN`. A strict audit additionally requires adjacent
FAST run IDs. Order-failed runs carry no capital and are not outcome runs.
Before any prior-run field is used, the previous funded run must have exited by
the current first-entry decision.

These are retrospective research labels. They are not live labels and cannot
be used as trading rules.

## Frozen causal assembly

All runs outside the `prior funded run = STOP_ONLY` state remain unchanged.
Only the next funded run can be reduced by the research policy. This prevents
the study from becoming another broad regime filter.

Two weighted logistic heads are assembled asymmetrically:

- tail head: Phase-1H compact continuous path plus causally known prior-run
  state;
- stop head: the same fields plus completed-H4 FAST/STD/SLOW HA;
- Wave is excluded because it failed the Phase-1H incremental gate.

The score is `P(tail journey run) - P(stop-only run)`. Prior-run state includes
known consecutive stop-only count, prior stopped units, prior R per funded unit,
FAST-run-ID gap, elapsed hours, prior outcome class, and direction.

## Train-only operating point

For each expanding fold, candidate thresholds are derived only from training-
run score quantiles. The selected threshold maximizes removed repeated stopped
units subject to all of these training constraints:

- retain at least 90% of all tail units;
- retain at least 85% of tail-journey runs;
- retain at least 80% of funded Children;
- retain at least 40% of runs following a stopped run.

The threshold is then applied unchanged to the later test fold. Test ranks,
outcomes, or economics cannot select the threshold.

## Success and scaling boundary

The primary policy must remove at least 40% of repeated stopped units pooled
and at least 15% in every fold. It must also remove at least 15% of all stopped
units pooled while retaining the frozen journey and frequency floors.

Child win rate must rise by at least three percentage points pooled. Raw net R
must stay positive in every fold. Because the user may increase size after a
genuine win-rate improvement, the report also computes an equal-stopped-budget
counterfactual. The scale factor is the baseline stopped-unit rate divided by
the policy stopped-unit rate. This is an arithmetic sensitivity, not executable
leverage authority; concentration, margin, costs, and nonlinear drawdown remain
outside it.

Required comparators are unchanged V10 participation, broad skip-after-stop
cooldown, and a perfect repeat-stop oracle upper bound. The broad cooldown is a
closed comparator, not a candidate rule.

## Authority boundary

All observations through `2026-09-18 23:57` are consumed development evidence.
GOLD# 2021 and post-cutoff chronology remain sealed. Phase 1I grants no entry,
veto, cooldown, exit, retry, capital, EA, or production authority.
