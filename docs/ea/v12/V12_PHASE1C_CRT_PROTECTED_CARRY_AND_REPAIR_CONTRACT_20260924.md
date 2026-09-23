# V12 Phase-1C CRT-protected carry and repair contract

Date frozen: `2026-09-24`

Status: `CONSUMED-DEVELOPMENT MECHANISM STUDY / FUTURE SHADOW DEFINITION / NO TRADE OR SIZING AUTHORITY`

Contract version: `v12-phase1c-crt-protected-carry-repair-v1`

## 1. Question

Phase 1C tests whether V10 used the wrong holding clock at some FAST-HA flips.
The experiment does not ask whether every NHA should be ignored. It asks:

1. when a selected V10 Child is aligned with a causal CRT Parent;
2. a completed opposite FAST-HA bar appears;
3. that same CRT Parent remains structurally active;
4. and no opposite CRT Parent is independently authorized;

does preserving the Child until its original Hard SL or the CRT Parent's end
retain more useful journey exposure than the frozen first-NHA exit?

The second question is whether the first completed FAST-HA return to the Parent
direction, while the same Parent still lives, defines a reproducible `REPAIR`
Child candidate.

## 2. Why this is not an NHA-ignore rule

The frozen V10 exit remains the comparator. Carry is available only inside the
same Phase-1B journey identifier and only for the two already-frozen transition
states:

- `OLD_JOURNEY_COUNTERFLOW`;
- `OLD_JOURNEY_AFTER_KEY_ARRIVAL`.

`OPPOSITE_CRT_AUTHORIZED`, `OLD_JOURNEY_FAILED_NO_OPPOSITE`, and
`NEUTRAL_ROTATION` never receive carry permission. A stopped Child remains dead,
its Hard SL is never widened, and no prior Child is resurrected.

## 3. Frozen populations

### 3.1 Selected-Child carry population

Start from the unchanged `ORIGINAL_FULL_R7G_PORTFOLIO`. A Child is carry-eligible
only when all of the following were known at its frozen FAST-NHA exit:

- its Phase-1B relation at entry was `ALIGNED_ACTIVE_JOURNEY`;
- the FAST flip maps to the same `journey_id` as the entry context;
- the flip state is one of the two old-journey states above;
- the Child reached the FAST-NHA exit without a Hard-SL touch or same-M1
  stop/exit ambiguity;
- the Parent has a later causal terminal timestamp or is explicitly censored at
  the source cutoff.

### 3.2 Repair episode population

One bridge episode begins at each unique eligible old-journey FAST flip. The
first later FAST flip is a repair only when:

- its new FAST direction equals the original Parent direction;
- its `active_journey_id` is the same original `journey_id`;
- it occurs before that Parent ends;
- the frozen V10 causal universe contains a valid k1 opportunity at that repair
  decision.

There is at most one repair candidate per bridge episode. Its entry and Hard SL
are the frozen V10 k1 coordinates, but its candidate reason is the CRT bridge
repair state, not HA color alone.

## 4. Predeclared policy views

Three selected-portfolio views are reported without changing entries or units:

1. `V10_BASELINE`: original first opposite FAST-HA exit;
2. `CRT_ACTIVE_CARRY`: carry every eligible Child to original Hard SL or Parent
   termination;
3. `CRT_UNFINISHED_TARGET_CARRY`: same carry only if the origin C1 opposite-edge
   target was still ahead at the NHA decision.

The third view is primary because CRT is a target-led journey grammar. The broad
active-only view is a mechanism control, not a candidate for promotion.

The origin opposite edge is open at decision time when it was forward-eligible
at Parent activation and its first touch is absent or not earlier than that
decision timestamp. A same-M1 touch is not treated as known before the decision.
No substitute target is invented after that edge is consumed. Older-liquidity
target succession requires a later contract.

Repair Children are reported separately as one-unit shadow candidates under the
same two views. They are not silently added to the selected R7G portfolio.

## 5. Exit and guard semantics

- Original entry, direction, Hard SL, and R7G units are frozen.
- Carry begins only after the baseline FAST-NHA execution M1, because the frozen
  universe already verified that minute did not touch the Child stop.
- Repair Child guarding begins on its entry M1.
- Chronological raw M1 tests Hard SL before the next review.
- Parent termination exits at the first M1 open at the causal terminal timestamp.
- If Hard SL and Parent termination occur in the same M1, score the Hard SL
  conservatively and record the Parent-open exit as the alternative.
- Gap stop behavior matches the V10 oracle: score the frozen stop price and flag
  the gap.
- An `OPEN_AT_CUTOFF` Parent produces a censored carry outcome and cannot enter
  closed-trade economics.

## 6. Required reporting

Report at minimum:

- eligible Children and unique bridge episodes;
- repaired, failed-before-repair, and censored episodes;
- changed stops, stopped units, weighted R, profit factor, right-tail units,
  maximum stop chain, drawdown, and concurrent funded units;
- annual, side, flip-state, and target-open breakdowns;
- repair-Child count, stop rate, R, and improvement versus its ordinary V10 k1
  exit clock;
- whether adding the repair Child improves direction-adjusted basket average
  entry, while keeping this descriptive rather than treating average price as
  edge;
- ambiguity and post-cutoff read counts.

Lower stop count caused only by fewer trades is not success. A carry rule can
increase Hard-SL count while improving R, or improve R while creating
unacceptable exposure; all dimensions remain visible.

## 7. Evidence boundary

The first build uses only the already-consumed chronology through
`2026-09-18 23:57` to test mechanism and implementation. It cannot promote an
action. The exact same semantics define the future shadow after that cutoff;
they must not be altered after later prices are observed.

`GOLD# 2021` remains sealed. No MQL5 parity, actual-tick economics, live sizing,
EA behavior, or production authority follows from this phase.
