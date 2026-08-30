# V8 Research Instructions

Status: `ACTIVE`
Generation: `V8`
Research family: `Causal Chart Representation / Event-Anchored Action Policy`
Production authority: `NONE`
EA authority: `NONE`

## 1. Purpose

V8 changes the representation problem, not merely the entry rule.

The project has repeatedly failed when ambiguous chart meaning was converted too early into hard labels or
scalar thresholds such as:

```text
TREND
RANGE
BREAKOUT
TURNING
HEALTHY_PULLBACK
TERMINAL_EXPANSION
```

These concepts may be useful to a human after looking at a chart, but they are not assumed to have a unique,
causally correct numerical definition.

V8 therefore tests a different claim:

> Preserve the causal chart geometry and precise numerical state, anchor decisions at objectively observable
> events, learn a latent representation of context, and evaluate actions directly without requiring a hard
> human market-state label first.

V8 is GOLD-only strategy research unless a later preregistered decision changes the market universe.

## 2. Core representation rule

Do not reduce ambiguous context to a manually invented state machine before learning.

The default V8 abstraction is:

```text
causal multi-timeframe chart geometry
+ precise numerical sequence
+ objectively observable event facts
+ current position/campaign facts
        ↓
learned latent context z_t
        ↓
action-conditioned future-path / utility estimates
        ↓
WAIT / ENTER / HOLD / ADD / REDUCE / EXIT
```

The latent representation does not need to be named `trend`, `range`, `breakout`, or `turning`.

Human vocabulary may be used later for explanation, retrieval, or qualitative audit. It is not decision
authority unless an independent experiment proves that a specific label is stable and useful.

## 3. Observable facts vs ambiguous interpretation

### Observable facts may be explicitly encoded

Examples:

- Double-B occurrence under the frozen mathematical detector;
- Bollinger-band touch/pierce;
- MA touch/cross/body-close relation;
- session opening timestamp;
- prior session high/low touch;
- causally confirmed swing or S/R interaction;
- candle OHLC geometry;
- spread and tick activity;
- current position, entry, stop-risk, realized/unrealized P/L;
- whether a prior entry/add/reduction actually occurred.

These are observations, not claims about market meaning.

### Ambiguous interpretations are not hard labels by default

Do not force labels such as:

- fresh trend;
- mature trend;
- range;
- healthy pullback;
- terminal extension;
- breakout Double-B;
- basic Double-B;
- turning Double-B.

A human may use these words in qualitative discussion, but the base model must not require them as targets
or rule gates.

## 4. Hybrid chart representation

V8 uses two complementary channels.

### Visual / geometric channel

Render causal multi-timeframe chart panels from information available at decision time only.

Initial panels:

```text
H1
M15
M5
M1
```

The renderer may include causally known overlays such as:

- Bollinger A / Bollinger B;
- selected moving averages;
- session boundaries;
- objectively detected event markers;
- causally confirmed S/R levels.

The purpose is to preserve spatial and temporal chart relationships that are easily destroyed by scalar
feature engineering.

### Numerical channel

Preserve exact quantities required for execution and risk:

- OHLC;
- spread;
- tick activity;
- exact indicator values;
- timestamp/session coordinates;
- current exposure;
- leg entries;
- stop-risk;
- realized and unrealized R;
- event metadata.

Visual input does not replace precise numerical accounting.

## 5. Causal rendering rules

Every rendered chart is part of the information boundary.

Therefore:

- no future candles may be visible;
- no future-confirmed swing may be drawn early;
- no axis or normalization may use a future global range;
- no future outcome annotation may enter the model input;
- indicator lines use only completed/causally available bars;
- event markers appear only when the event would actually be known;
- train/validation preprocessing must not fit on future data.

A visually attractive chart is invalid if its construction leaks future information.

## 6. Event anchors

V8 does not require every minute to be an independent trade signal.

Events are decision anchors: moments at which the current chart deserves re-evaluation.

Initial observable anchor families may include:

```text
Double-B confirmation
MA touch / cross / body-close interaction
Bollinger touch / pierce / re-entry
session-open and prior-session-boundary interaction
causally confirmed S/R touch / break / retest
large displacement / activity shock
position-management milestones
```

Double-B is a privileged research anchor because V7 already developed detector and contextual knowledge, but
it is not the only possible V8 event.

The event itself does not determine LONG/SHORT.

## 7. Decision problem

V8 does not primarily train a generic `future return is up/down` classifier.

The research target is the economic consequence of available actions under the current latent context.

When flat, the minimal action set is:

```text
WAIT
ENTER_LONG
ENTER_SHORT
```

When long:

```text
HOLD
ADD_LONG
REDUCE_LONG
EXIT_LONG
```

When short:

```text
HOLD
ADD_SHORT
REDUCE_SHORT
EXIT_SHORT
```

A later stage may add finer reduction sizes or risk actions only after the simpler action set is understood.

## 8. Action-conditioned future path

The model/research harness should estimate information relevant to actual trade management, such as:

- MAE distribution;
- MFE distribution;
- probability/time to reach risk multiples;
- probability/time to structural failure;
- path after a pullback/retest;
- path conditional on continuing to hold;
- cost of changing exposure;
- future opportunity to add/reduce.

The goal is not to manufacture a single magical score.

## 9. Campaign accounting

Multiple entries inside one move are allowed only as explicit campaign actions.

Do not repeat the old error of counting overlapping signals as independent winning trades.

For every campaign record:

- each leg and timestamp;
- each leg's initial stop-risk;
- total simultaneous exposure;
- realized partial P/L;
- remaining position;
- add/reduce reason/action;
- campaign maximum risk;
- campaign net R;
- campaign risk-normalized return;
- maximum adverse excursion;
- maximum favorable excursion.

A high-frequency system must earn its frequency through genuine sequential opportunities, not duplicate
counting of one underlying move.

## 10. Indicators

Indicators are allowed as representations, overlays, and exact observed variables.

Do not assume:

```text
ADX high = trend
RSI overbought = short
CCI extreme = reversal
MA slope > threshold = breakout
```

The value of an indicator may depend on the whole chart context.

V8 specifically allows the model to learn those conditional relationships without requiring a fixed
human-written interpretation first.

## 11. V7 relationship

V7 is paused and preserved as semantic/research history.

V8 inherits useful observable machinery from V7, including:

- Double-B detector semantics;
- Bollinger definitions;
- KTR/session concepts when causally available;
- S/R and target-room lessons;
- campaign-risk warnings;
- the finding that Double-B side alone is not direction.

V8 does **not** inherit BASIC/BREAKOUT/TURNING as mandatory classifier labels.

Do not retrospectively rewrite V7 results.

## 12. V4 relationship

V4 correctly identified the representation-level problem:

```text
human-defined state -> rule
```

should be challenged by:

```text
causal sequence -> learned latent state -> policy
```

V8 does not simply reopen V4.

Differences:

- GOLD-only strategic objective;
- visual chart geometry is first-class input;
- event-anchored decision points;
- action-conditioned path/campaign problem rather than generic next-return prediction;
- explicit add/reduce/hold/exit lifecycle;
- V7 chart semantics used as observable context, not hard market-state labels.

## 13. Data roles

All GOLD# 2022-2026 evidence is considered open/consumed for V8 development because these years have already
been inspected by prior research or the current project.

They may be used for chronological development diagnostics, but not claimed as pristine final validation.

Current untouched reserve recorded by the repository:

```text
GOLD# 2021
```

Do not open GOLD# 2021 until a V8 candidate, preprocessing pipeline, model selection protocol, action policy,
and evaluation procedure are frozen.

## 14. Research progression

### V8-001 — Causal representation foundation
Build and verify chart renderer, numerical stream, event anchors, campaign state and strict information boundary.

### V8-002 — Representation / retrieval diagnostics
Test whether learned representations preserve recurring chart-context information better than hand-engineered
scalar baselines. Use nearest-neighbor retrieval and future-hidden diagnostics.

### V8-003 — Action-conditioned path model
Estimate future path consequences of flat/long/short and simple campaign actions.

### V8-004 — Sequential campaign controller
Evaluate one-position/campaign replay with costs and explicit exposure accounting.

### V8-005 — Freeze
Freeze the representation, event population, controller and risk architecture.

### V8-006 — Untouched validation
Only after V8-005, open the untouched temporal reserve.

## 15. Hard restrictions

Do not:

- create a new hard `TREND/RANGE/BREAKOUT/TURNING` classifier merely to make the problem look interpretable;
- tune arbitrary visual window lengths from P/L without a preregistered reason;
- allow future information into chart rendering;
- optimize on the untouched reserve;
- count overlapping same-move decisions as independent trades;
- report event-level expectancy as campaign expectancy;
- use a black-box model without same-input baselines and ablations;
- promote a model because one year/session looks good;
- use RL to rescue a representation with no demonstrated information value;
- modify production EA logic from V8 development results.

## 16. Final strategy requirements

The project goal remains demanding:

- realized win rate at least 50%, with the research objective materially higher;
- average positive payoff meaningfully above 1R and preferably near/above 2R;
- clearly positive full-cost expectancy;
- target final average net expectancy of approximately +1R/trade if evidence supports it;
- multiple executable opportunities when the chart legitimately presents them;
- acceptable drawdown, exposure and loss-streak behavior;
- no hidden hindsight or duplicate-event inflation.

Frequency is an objective, not permission to lower evidence quality.
