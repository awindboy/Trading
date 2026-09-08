# V9 February 2025 Causal Replay Addendum

Date: `2026-09-08`  
Status: `ACTIVE DEVELOPMENT EVIDENCE`  
Market: `GOLD# ONLY`  
Evidence class: `FUTURE-HIDDEN SEQUENTIAL REPLAY / DESCRIPTIVE`  
Production authority: `NONE`  
EA authority: `NONE`  
Untouched reserve: `GOLD# 2021`  
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

This document continues:

`V9_PARENT_CHILD_REPLAY_202502.md`

and preserves the February state recovered after the previous replay session reached its conversation limit.

---

## 1. Causal boundary

The current authorized replay boundary is:

```text
2025-02-20 10:30:00
```

No price action after that timestamp belongs to the current research state.

PAPER-016 remains OPEN.

Do not retrospectively insert trades into intervals skipped because the reveal cadence exposed too much future information.

---

## 2. February trade state

Through the current causal boundary:

```text
PAPER-001 ... PAPER-015 = CLOSED
PAPER-016                 = OPEN
```

Closed child outcomes:

```text
structural positive = 8
structural loss     = 7
open                = 1
```

This must NOT be reported as an execution-valid 53.3% win rate.

Reasons:

- 2025 exact Bid/Ask tick authority is unavailable;
- spread/slippage are not fully represented;
- intraminute ordering can matter;
- small structural positives such as PAPER-011 may differ after real costs.

The correct interpretation is:

```text
decision-replay evidence = 8 positive / 7 loss / 1 open
```

not validated economic performance.

---

## 3. Closed-trade summary

| Trade | Direction | Family | Descriptive result | Primary lesson |
|---|---|---|---|---|
| 001 | LONG | local / CP1 | +1.3R to +2.0R | repair inside damaged parent can still be a good child pitch |
| 002 | LONG | local / CP1 | +2.0R to +2.7R | same parent campaign can produce another independent opportunity |
| 003 | LONG | OPEN ROUTE | -0.6R to -1.1R | open-route child failed without automatically killing parent |
| 004 | LONG | local | ~-1.25R | child invalidation and parent survival remain separate |
| 005 | LONG | local | -1.2R to -1.7R | repeated child failure can eventually damage parent belief |
| 006 | LONG | OPEN ROUTE | ~+3R / +1.48S | first strong structural runner |
| 007 | SHORT | local | ~-1R to -2R | large downside traversal did not prove bearish parent |
| 008 | SHORT | counter-parent | +1.2R to +1.8R | counter-parent child can be a good trade |
| 009 | SHORT | counter-parent | +1.4R to +2.5R | child win still does not prove parent direction |
| 010 | LONG | OPEN ROUTE | ~+4R or better descriptive | strong continuation capture |
| 011 | LONG | OPEN ROUTE | small positive | large MFE but severe capture latency |
| 012 | SHORT | failed repair | +1.3R to +2R | clean local opportunity while parent remained uncertain |
| 013 | LONG | OPEN ROUTE | -0.8R to -1.2R | false continuation |
| 014 | LONG | OPEN ROUTE | -0.8R to -1.2R | repeated false continuation |
| 015 | LONG | OPEN ROUTE | -1.5R to -2R | known-high consumption followed by failure |
| 016 | LONG | OPEN ROUTE | OPEN | current frozen child |

For exact PAPER-001 through PAPER-014 chronology, entries, anchors, and Parent Ledger transitions, use `V9_PARENT_CHILD_REPLAY_202502.md`.

---

## 4. PAPER-015 evidence boundary

The recovered review preserves only:

```text
Direction: LONG
Family: OPEN ROUTE
Result: structural loss
Descriptive result: approximately -1.5R to -2R
Context: known-high consumption followed by continuation failure
```

The available surviving source does NOT support reconstruction of an exact timestamp, exact entry, exact S, or exact anchor.

Do not manufacture those fields.

PAPER-015 remains useful principally as a member of the failed OPEN ROUTE matched set.

---

## 5. PAPER-016 frozen state

### V9-2025FEB-PAPER-016

```text
Time: 2025-02-20 09:00
Direction: LONG
Type: OPEN ROUTE continuation
Entry: ~2946.8
Fixed TP: none
Status: OPEN
```

Working child anchor:

```text
2944-2945
```

Functional falsification:

```text
genuine re-loss of 2944-2945
+
failure to recover 2946-2947 business
```

`2947-2948` was observed only as a possible candidate memory.

It had NOT earned enough authority by the 10:30 cutoff to replace the official working anchor.

Observed through the causal cutoff:

```text
MFE: ~2954.73
2025-02-20 10:30 current: ~2954.17
```

Parent working belief:

```text
upper journey is currently more coherent,
but endpoint is unknown,
and PAPER-016 success or failure cannot prove parent direction.
```

---

## 6. PAPER-016 H4 ATR correction

The recovered frozen note contained:

```text
S ≈ 9.90
```

and consequently described the initial structural distance and favorable excursion using that coordinate.

A later authority audit reproduced the established February H4 Wilder ATR convention against the authoritative M1.

Definition:

```text
S(t) = previous fully completed H4 Wilder ATR14
```

The same calculation reproduced prior frozen February values:

```text
PAPER-001  recorded ~12.34 -> recomputed ~12.34
PAPER-002  recorded ~12.74 -> recomputed ~12.74
PAPER-012  recorded ~18.06 -> recomputed ~18.06
PAPER-013  recorded ~16.51 -> recomputed ~16.51
PAPER-014  recorded ~15.34 -> recomputed ~15.34
```

At PAPER-016 entry, `2025-02-20 09:00`, the previous completed H4 bar is the H4 period beginning `04:00`.

Correct coordinate:

```text
S = 14.26401609770702
```

Therefore the old `S ≈ 9.90` value is superseded.

This is a coordinate correction only.

It does NOT change:

- the LONG decision;
- entry ~2946.8;
- 2944-2945 working anchor;
- falsification logic;
- OPEN status;
- Parent Journey working belief;
- the causal boundary.

Corrected descriptive coordinates:

```text
entry -> 2944-2945 anchor distance
≈ 0.13S to 0.20S

entry -> MFE 2954.73
≈ +0.56S

entry -> 10:30 price 2954.17
≈ +0.52S
```

The prior notes of approximately `0.18-0.28S` risk and `+0.8S` MFE were consequences of the incorrect S and are not current authority.

---

## 7. Main February finding

February did not show that V9 became much better at predicting market direction.

It showed something more compatible with the V9 objective:

```text
take a good attempt
accept bounded child failure
preserve the larger market understanding separately
remain available
take another independently justified attempt
allow some winners to travel farther
```

The important evidence is not merely the 8:7 outcome count.

The important change is continuity.

January V9 often behaved like:

```text
good local trade
-> destination
-> local trade finished
-> larger story nearly reset
```

February increasingly behaved like:

```text
Parent Journey
   -> child attempt
   -> child resolves
   -> parent updated separately
   -> wait
   -> another independent child opportunity
```

This is the first substantial future-hidden evidence that the desired campaign-like trading behavior is possible without converting Parent Journey into a mechanical direction filter.

---

## 8. Child loss != parent death

PAPER-003 -> PAPER-004 -> PAPER-005 -> PAPER-006 is the central stress case.

The correct interpretation was not:

```text
first LONG loss
=> bullish idea false forever
```

and not:

```text
parent may survive
=> refuse to stop LONG children
```

Instead:

```text
each child dies when its own thesis dies
+
parent working belief is updated separately
```

Repeated failures materially weakened the upper story.

Subsequent market repair created a new child thesis.

PAPER-006 then became a new good attempt and produced the first major structural runner.

This is exactly the separation V9 is trying to preserve.

---

## 9. Good child trade != parent-direction truth

PAPER-008 and PAPER-009 were successful local SHORT attempts while the larger upper repair remained meaningful.

Afterward the market expanded strongly upward.

Therefore:

```text
good SHORT
!=
bearish parent proven
```

The local opportunity and larger journey must remain separate research objects.

---

## 10. Larger capture became possible

PAPER-006:

```text
entry ~2840.9
exit reference ~2861.8
captured ~20.9 dollars
~+1.48S
~+3R descriptive
```

PAPER-010:

```text
entry ~2888.2
exit ~2901-2902
captured ~13 dollars
~+0.8S
~+4R or better descriptive
```

These are the first strong sequential examples in which:

```text
close structural falsification
+
open upside participation
```

coexisted.

This is important evidence, but not a frozen exit rule.

---

## 11. Capture latency remains unresolved

PAPER-011:

```text
entry ~2922.7
MFE ~2942.55
favorable excursion ~19.8 dollars
actual structural capture only ~1-3 dollars
```

Waiting for structural failure preserved the no-top-prediction philosophy but returned most of the available move.

Therefore:

```text
fixed TP is not the final answer
```

but also:

```text
structural trailing is not automatically the final answer
```

The research question is not:

> How can we exit at the top?

It is:

> Can normal continuation pullback and genuine degradation of the child journey be distinguished earlier without requiring top prediction?

---

## 12. OPEN ROUTE warning

Closed OPEN ROUTE subset:

```text
Positive:
006
010
011

Loss:
003
013
014
015
```

This is:

```text
3 positive
4 loss
n = 7
```

Do not freeze a hit rate, payoff model, or OPEN ROUTE rule from this set.

The consecutive 013-015 failures are an important falsification set.

Possible failure mode:

```text
old upper memory consumed
-> pullback
-> small reaction
-> reaction promoted too easily to "earned new anchor"
-> LONG
-> continuation failure
```

The next question is NOT:

```text
how many retries should be allowed?
```

It is:

```text
is this genuinely a new thesis,
or is the previous failed breakout thesis being renamed and revived?
```

No retry limit should be introduced yet.

---

## 13. Parent continuity vs narrative persistence

Parent Journey improved continuity, but creates a new danger.

The phrase:

```text
parent is still alive
```

must never become a narrative excuse for repeatedly taking the same failed idea.

Parent belief must be allowed to:

- survive a child failure;
- accumulate damage;
- repair;
- become unresolved;
- switch when evidence materially changes.

A surviving Parent Journey does not itself authorize another child trade.

Every new child must still earn independent thesis authority.

---

## 14. NO TRADE and missed opportunities

February produced more attempts without forcing frequency.

Notably:

```text
2025-02-17 = 0 trades
```

despite substantial market movement.

Several other potential moves were intentionally excluded because coarse reveal cadence had already exposed too much future information.

Examples included:

- continuation after PAPER-006;
- some large downside translation;
- a later 2/13 LONG opportunity;
- a large 2/14 SHORT leg.

These must NOT be backfilled.

Therefore the February result set is:

```text
the causally observed subset
```

not the maximum hypothetical performance V9 could have produced.

Do not calculate validated monthly Profit Factor or expectancy from this replay.

---

## 15. Immediate continuation contract

Do not alter the trading protocol before February is completed.

Current state:

```text
CUTOFF: 2025-02-20 10:30
PAPER-016: OPEN LONG
ENTRY: ~2946.8
WORKING ANCHOR: 2944-2945
S: 14.26401609770702
```

Next authorized reveal:

```text
after 2025-02-20 10:30
```

The next normal replay checkpoint may be `10:45`.

Manage PAPER-016 using only newly revealed information.

Do not use the S correction to alter the already frozen trade thesis.

---

## 16. Research after February completes

Do not add a new indicator, score, EA rule, trend filter, retry limit, or fixed ATR threshold.

Run two separate archaeology studies.

### A. OPEN ROUTE entry matched pairs

Positive:

```text
006
010
```

Capture-latency positive:

```text
011
```

Failures:

```text
003
013
014
015
```

Compare market role rather than outcome-selected numeric features.

Questions:

- Was the prior memory genuinely consumed or only traversed?
- Did price establish new business/value after consumption?
- Was the pullback anchor truly earned by departure and return behavior?
- Was a small reaction promoted too early to memory authority?
- How much unresolved damage existed in the Parent Journey?
- Was the route genuinely open or did meaningful memory still remain nearby?
- Did winner and loser departures perform different market roles?

### B. Winner capture archaeology

Cases:

```text
006
010
011
```

Question:

> Without predicting the terminal top, can V9 distinguish a normal pullback from genuine continuation failure with less capture latency?

Keep entry and exit research separate.

---

## 17. Decisions added by this stage

### V9-068
February causal replay is development evidence, not untouched validation or exact execution authority.

### V9-069
Parent Journey remains continuity context and must not become a mandatory direction gate.

### V9-070
Child invalidation remains independent from Parent Journey invalidation.

### V9-071
A successful child trade must not be interpreted as proof of parent direction.

### V9-072
OPEN ROUTE continuation remains research-active but unformalized. PAPER-013-015 are mandatory counterexamples.

### V9-073
Do not add retry limits, breakout scores, ATR thresholds, trend filters, or other numerical rescue rules from the current February sample.

### V9-074
PAPER-011 preserves capture latency as an unresolved exit problem.

### V9-075
PAPER-016 historical `S≈9.90` is corrected to `S=14.26401609770702` from authoritative M1 using the established previous-completed H4 Wilder ATR14 convention. This correction has no authority over the already frozen trade decision.

### V9-076
The February replay must be completed under the unchanged discretionary protocol before OPEN ROUTE or exit findings are promoted.

---

## 18. Causal replay harness

`/scripts/v9_causal_m1.py` is research instrumentation only.

Its job is to protect causal integrity, not to generate trading decisions.

Required behavior:

- verify authoritative M1 SHA256;
- require an exact requested cutoff timestamp;
- write only the revealed prefix;
- preserve a byte offset for incremental continuation;
- verify the revealed-prefix hash before advancing;
- fail closed if source or revealed history changes;
- construct higher-timeframe snapshots only from revealed M1;
- report previous-completed H4 Wilder ATR14;
- never affect entry, SL, TP, sizing, or lifecycle decisions.

The harness does not constitute V9 strategy formalization.

---

## 19. Formalization status

```text
CLOSED
```

No V9 EA or production strategy exists.

February is still active discretionary research.

The immediate objective remains:

> Build a trader that repeatedly takes worthwhile swings under uncertainty, kills failed child theses without denial, preserves larger context without narrative attachment, and stays available when a meaningful market journey continues.