# V7-002 Outcome-Informed Reverse Engineering Results

Status: `CONSUMED DISCOVERY / HINDSIGHT ONLY`
Date: `2026-08-30`
Validation authority: `NONE`

## 1. Why this experiment was done

An initial automated Double-B shadow test was too simplistic.
It implicitly treated Double-B side/candle form as a direction rule and used fixed KTR mechanics.

The user corrected the interpretation:
- Double-B is a rare-event detector;
- direction must come from context;
- many context elements are discretionary;
- KTR SL/TP multiples must adapt to market state;
- staged entry is a separate risk architecture.

A second 24-event visual pilot hid the future and asked the AI to decide directly from the H1 chart.
That pilot failed materially.

The future was then deliberately opened to reverse engineer what the events actually meant.

## 2. Consumed sample

24 events:
- GOLD#: 8
- BTCUSD#: 8
- USDJPY#: 8
- 4 upper and 4 lower Double-B events per market.

The exact event records are stored in:
`ledgers/v7/V7_002_RETROSPECTIVE_EVENT_LEDGER.csv`.

## 3. Blind visual pilot

Before outcome reveal:
- LONG / SHORT / SKIP decisions were recorded;
- event-specific KTR SL/TP choices were recorded;
- 0.5-KTR staged-entry plans were recorded where selected.

Result on resolved trades:

```text
N = 18
positive campaigns = 6
positive rate = 33.33%
campaign net = -32.88R
campaign EV = -1.826R
average filled legs = 4.44
worst campaign = -7R
```

The initial-leg-only diagnostic was also negative.

Interpretation:
- failure was not only caused by staged entry;
- the real-time contextual classification itself was poor;
- equal-risk-per-leg staging amplified wrong theses.

This pilot is a method check, not a method falsification.

## 4. Outcome-informed reverse engineering

Future path was then revealed for all 24 events.

Each event was re-examined with two columns kept conceptually separate:

1. what evidence existed at the event close;
2. what future path later showed.

Events that could not reasonably have been classified at the close were left as:
`WAIT_CONFIRM` or `SKIP`.

They were **not** forced into perfect hindsight immediate entries.

## 5. Central discovery

The main classification problem is:

```text
FRESH EXPANSION    -> BREAKOUT
RANGE EXTREME      -> BASIC
TERMINAL EXPANSION -> TURNING
INSUFFICIENT INFO  -> WAIT / SKIP
```

This is more informative than:
- upper/lower DB side;
- candle color;
- outside-band close alone.

## 6. Outside-band body close is not direction authority

In the consumed sample, strong closes beyond both bands appeared in both:
- genuine continuations,
- and terminal/climactic reversals.

Examples:

### GOLD-01
A genuine bullish breakout:
- strong body;
- outside-band close;
- session/structure break;
- +2KTR reached quickly;
- +3KTR was not reached before reversal.

Lesson:
direction was right; target was wrong.

### USDJPY-04
A bearish-looking outside-band close in a HIGH-KTR extreme candle.
Future path quickly reversed upward.

Lesson:
the same visual "strength" can represent capitulation/terminal expansion.

### BTCUSD-08
Large bullish blow-off outside the bands.
Price briefly extended, then collapsed massively.

Lesson:
a terminal push can look strongest at the exact point continuation quality is worst.

### USDJPY-03
Strong sustained downside continuation occurred even without requiring the canonical
close-beyond-both-bands condition.

Conclusion:
outside-band close is evidence, not classifier.

## 7. KTR lessons

KTR should measure the event's scale.

It should not mechanically dictate a stop multiple.

### LOW KTR can still use a tight stop
`USDJPY-01` had clean trend continuation and needed only small adverse excursion.

### LOW KTR can also justify wider structural room
`GOLD-04` pulled back roughly 1.57KTR before delivering a strong downside move.
A wider structural stop and planned pullback entries were coherent.

### HIGH KTR can require smaller KTR multiples
`USDJPY-04` and `GOLD-07` showed that a large absolute KTR makes large-multiple stops/targets
economically and structurally excessive.

Thus:

```text
STRUCTURE -> price invalidation
KTR -> normalized interpretation of that distance
```

not the reverse.

## 8. Staged-entry lessons

Automatic 0.5-KTR adding is rejected as a generic rule.

Better interpretation:

### Momentum breakout
Usually no blind averaging.
Deep adverse movement may invalidate the thesis.

### Planned breakout pullback
Staging can be coherent if the retracement was expected before the first order.

### BASIC
Zone entry can be coherent because excursion into the range edge is part of the thesis.

### TURNING
Prefer confirmation/reclaim before building size.
Blind averaging into an unconfirmed fade is especially dangerous.

## 9. Target selection matters as much as direction

Several blind-pilot losses initially moved in the predicted direction.

Examples:
- GOLD-01: +2KTR available, +3KTR not.
- GOLD-02: initial short scalp worked before later reversal.
- BTCUSD-01: bullish extension worked before a much larger reversal.
- USDJPY-06: +1KTR rebound was clean; a larger target required excessive heat.

Therefore V7 must explicitly estimate:
`remaining structural room / current KTR`.

A correct direction with a poor target is still a bad trade plan.

## 10. Two-stage events

A Double-B can begin one phase and later become another.

Example conceptual sequence:

```text
initial breakout
-> breakout failure / reclaim
-> new turning setup
```

The second trade must be a new causal decision with its own confirmation.
It cannot be retroactively bundled into the first Double-B call.

## 11. Conservative hindsight plan result

After future-informed event-by-event planning, a conservative execution calculation was run:

- WAIT_CONFIRM events without exact confirmation logic were kept at 0R;
- SKIP stayed 0R;
- unspecified runners were excluded;
- unspecified second reversal trades were excluded;
- only explicitly recorded SL/TP/staging plans were executed.

Result:

```text
24 total discovery events
19 hindsight-planned trades
19 wins
0 losses
+89.03R campaign_R_sum
+4.69R average per traded campaign
28 filled legs
```

Single-entry-only version:

```text
+46.76R
```

The extra roughly +42.27R came from event-specific staged-entry plans.

### Critical interpretation

`+89.03R` is **not a strategy backtest**.

It is a hindsight upper-bound diagnostic:
the future was used to decide which event was breakout/basic/turning/wait,
how wide the stop should be,
how far the target should be,
and where staging was appropriate.

100% WR is therefore evidence of hindsight flexibility, not edge.

The research question is now:

> How much of this hindsight plan quality can be recovered when the future is hidden?

## 12. Discovery hypotheses carried into V7

Allowed as hypotheses only:

1. Double-B is an event detector, not a direction rule.
2. Fresh expansion vs terminal expansion is the core breakout/turning distinction.
3. Outside-band close is neither necessary nor sufficient for breakout.
4. WAIT_CONFIRM must be a first-class action.
5. KTR is a distance coordinate system, not a fixed SL/TP formula.
6. Target room should be assessed relative to both structure and KTR.
7. Momentum breakout should not use blind averaging.
8. Planned pullback/basic setups may justify staged entry.
9. Turning setups need stronger confirmation before adding exposure.
10. One Double-B can lead to multiple later states, but every later trade needs a new causal trigger.

## 13. What is explicitly NOT learned

Do not promote:
- `HIGH KTR -> TURNING`;
- a fixed body/KTR threshold;
- a fixed SL/TP table by KTR quartile;
- the exact hindsight KTR multipliers in the event ledger;
- the exact 19 hindsight trades as a performance estimate.

All 24 events are consumed.
