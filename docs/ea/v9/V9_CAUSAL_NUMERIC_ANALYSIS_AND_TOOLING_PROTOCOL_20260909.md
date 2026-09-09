# V9 Causal Numeric Analysis and Tooling Protocol

Date: `2026-09-09`
Status: `ACTIVE EXECUTION / ANALYSIS TOOLING AUTHORITY`
Scope: `HOW V9 IS OBSERVED AND EXECUTED, NOT A NEW MARKET EDGE`
Market: `GOLD# ONLY`
Authoritative M1 SHA256: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`

## 1. Why this protocol exists

V9 already defines the trading strategy and the compliance harness.

A separate problem remains:

```text
same strategy documents
+ different observation tools / chart representation
=> materially different discretionary decisions
```

An AI that reads scaled candlestick images, an AI that reads raw OHLC tables, and an AI that scans a large dataframe can all claim to follow the same strategy while receiving materially different perceptual inputs.

This protocol standardizes the **representation, reveal mechanism, timeframe escalation, exact-price handling, and observation semantics** used by V9 sessions.

It does not define a new entry pattern, score, threshold, trend classifier, or predictive model.

Permanent separation:

```text
STRATEGY AUTHORITY
= what counts as Parent / Child / good pitch / falsification / lifecycle

COMPLIANCE HARNESS
= questions proving the strategy was applied fairly

TOOLING / OBSERVATION PROTOCOL
= exactly what causal market information the AI is allowed to inspect and in what representation
```

All three layers must agree before a session can claim faithful V9 execution.

---

## 2. Canonical perceptual input: numeric OHLC, not chart images

### 2.1 Primary representation

The primary market representation is **numeric OHLC time series reconstructed from the authoritative raw M1 chronological prefix**.

Canonical fields:

```text
timestamp
open
high
low
close
```

The current V9 discretionary replay does **not** use candlestick-chart images as primary trade authority.

The reason is not that images are inherently inferior. It is that visual judgment can change materially with:

- y-axis range;
- chart width / number of visible bars;
- zoom;
- candle body pixel size;
- vertical compression;
- auto-scaling after a large wick;
- screen aspect ratio;
- renderer differences.

Terms such as `steep`, `extended`, `small pullback`, or `large candle` can become accidental functions of rendering scale.

Numeric price/time representation removes most of that uncontrolled visual degree of freedom.

### 2.2 Image rule

Images may be used only as **supplemental visualization**.

An image must never be the sole source for:

- Parent direction;
- Child recognition;
- structural falsification;
- Hard SL;
- candidate rejection;
- campaign exit;
- `too extended` / `too late` judgment.

If an image suggests something material, the decision rationale must be restated using the canonical numeric prefix: actual highs/lows, closes, settlement migration, repair/departure sequence, or consumed memories.

If image perception and numeric evidence conflict, **numeric causal evidence has authority**.

### 2.3 No visual-angle authority

Do not infer trend strength from the screen angle of a plotted line or candle sequence.

```text
visual slope / angle != market evidence
```

Use actual price displacement, time elapsed, H1/H4 distance context, settlement behavior, and `S` only as authorized.

---

## 3. Raw data authority and clock

### 3.1 Raw source

Authoritative raw M1:

```text
SHA256 626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2
```

Expected columns:

```text
<DATE> <TIME> <OPEN> <HIGH> <LOW> <CLOSE> <TICKVOL> <VOL> <SPREAD>
```

The file is tab-separated.

### 3.2 Source clock is preserved

Use the timestamps exactly as recorded by the data source.

Do **not** convert them to Seoul time, UTC, or another timezone for replay analysis.

All M15/H1/H4 bucket boundaries are anchored to the **source/broker clock**.

### 3.3 Decision-authority fields

Current V9 price-structure decisions use OHLC.

`TICKVOL`, `VOL`, and `SPREAD` are not current discretionary signal authority.

The raw spread field does not make 2025 M1 equivalent to exact historical Bid/Ask tick execution.

Do not claim exact slippage/spread-adjusted fills from this replay.

### 3.4 No synthetic missing minutes

Do not interpolate missing rows.

A market/session gap remains a gap.

Higher-timeframe aggregation uses only the raw rows that actually exist in the causal prefix.

---

## 4. Causal prefix is a hard tool boundary

### 4.1 State model

A causal replay state must minimally contain:

```text
source_path
source_sha256
revealed_cutoff
source_byte_offset
revealed_cache_path
position state
open trade Hard SL / destination if applicable
current review mode
known contaminated intervals
```

The key property is monotonicity:

```text
next_cutoff >= current_cutoff
```

Never reveal future price rows and then pretend to return to an earlier decision state.

### 4.2 Do not preload the full future file into an analysis dataframe

The canonical helper must not use a workflow equivalent to:

```python
all_data = pandas.read_csv(full_future_file)
then filter all_data <= cutoff
```

Even if the AI is not intentionally shown later rows, that design unnecessarily places future prices inside the active analysis process and makes accidental leakage easier.

Instead, stream the source chronologically and stop at the causal boundary.

### 4.3 Future-row timestamp peeking

To know whether the next row is beyond the target cutoff, the helper may read only the next row's timestamp fields.

If that timestamp is later than the target, rewind to the start of that row **without reading its future OHLC values**.

This is the preferred fail-closed behavior.

### 4.4 Exact cutoff semantics

`revealed_cutoff` means:

> the latest source timestamp whose complete M1 OHLC row has been exposed to the discretionary decision process.

No decision may use a price after that timestamp.

---

## 5. Canonical timeframe construction

All higher timeframes are reconstructed from the revealed M1 prefix.

Uploaded M5/M15/M30/H1/H4 files may be used only for parity checks or acceleration when their entire bar is already behind the causal cutoff. The **default and dispute authority is raw-M1-derived aggregation**.

### 5.1 Clock buckets

Use source-clock buckets:

```text
M15:  hh:00-14, hh:15-29, hh:30-44, hh:45-59
H1:   hh:00-59
H4:   00:00-03:59, 04:00-07:59, 08:00-11:59, ...
```

For each bucket:

```text
OPEN  = first revealed M1 open in bucket
HIGH  = max revealed M1 high in bucket
LOW   = min revealed M1 low in bucket
CLOSE = last revealed M1 close in bucket
```

### 5.2 Completed bars only

Normal strategy review uses **fully completed** bars only.

Examples:

```text
07:45 M15 becomes complete at 07:59
07:00 H1 becomes complete at 07:59
04:00 H4 becomes complete at 07:59
```

Do not use the future remainder of an unfinished higher-timeframe candle.

The current M1 row at the cutoff is allowed for exact execution/falsification work because it is itself fully revealed.

### 5.3 No candle-image reconstruction requirement

The AI does not need to render a visual candlestick to reason about the bar.

The canonical H1 row is text such as:

```text
2025-06-10 14:00  O=3335.34 H=3342.52 L=3332.23 C=3333.65
```

A sequence of such rows is the primary perceptual object.

---

## 6. Canonical numeric context packet

A session should preserve older active memories explicitly, while using a bounded recent numeric window for immediate perception.

Recommended default display windows:

```text
H4:  last 20 completed bars
H1:  last 24 completed bars
M15: last 16 completed bars when candidate/position warning is active
M5:  last 12 completed bars only when execution detail is needed
M1:  exact rows around entry / SL / destination / manual-exit ambiguity
```

These are **display windows, not market thresholds**.

Older relevant Parent/Child memories are not forgotten merely because they leave the recent window. They must persist in the causal state as named active memories.

### 6.1 Numeric reading priority

Read in this order:

1. actual new favorable/adverse extremes;
2. H1/M15 close / settlement sequence;
3. repeated survival or consumption of relevant areas;
4. repair and departure sequence;
5. relation to retained active memories;
6. only then supplemental indicator/location information.

### 6.2 Settlement ladder

A core object in the current analysis is the sequence of closes, for example:

```text
H1 closes: 3305.49 -> 3310.82 -> 3312.16
```

This is interpreted as actual adverse settlement migration for an open SHORT.

The sequence matters more than whether a rendered candle body happens to look visually large or small.

---

## 7. What `Parent`, `Child`, and market roles look like in numeric data

This section describes the observation mechanism. It does not convert V9 into a pattern checklist.

### 7.1 Parent observation

Parent Journey is primarily read from H1/H4 continuity using:

- successive favorable/adverse extremes;
- where H1 settles relative to recent business;
- whether value/settlement migrates over multiple completed bars;
- whether counterflow survives long enough to establish its own business;
- whether damaged route/value is repaired;
- whether important prior memories are consumed or rejected.

Parent is **not** assigned from a single moving-average direction, one breakout candle, or a visual trendline.

### 7.2 Child observation

A Child is the **current tradable attempt / route**, usually read on M15/H1.

It is not merely:

> a price level where a reaction is expected.

A level can matter, but the Child is what the market is currently **doing around and away from that area**.

Useful functional observations include:

```text
hold
repeated hold
new business
repair
repair failure
reclaim
departure
return / reuse
auction relocation
value translation
```

No one sequence is mandatory.

### 7.3 How those words are read numerically

`hold`:
- price revisits/pressures a relevant area but does not establish contrary settlement through it;
- judged from actual highs/lows/closes, not a visual support line thickness.

`departure`:
- price does not merely wick away; subsequent settlement/business moves away enough that the active route has changed meaningfully.

`repair`:
- counterflow reclaims part of previously lost route/value.

`repair failure`:
- the repair reaches a meaningful prior area but cannot maintain that reclaimed business and the prior route resumes.

`reclaim`:
- price does more than touch a lost area; settlement/business returns to the other side with functional persistence.

`new business`:
- price trades and settles in an area that materially extends or relocates the active route, rather than producing only an isolated wick.

These remain discretionary role descriptions. There is no mandatory bar count, percentage, ATR amount, or candle-shape template.

---

## 8. Active memory handling

The current method does not run an automatic support/resistance detector.

Memories are retained because they previously performed a meaningful role.

Typical active memory labels:

```text
Parent favorable extreme
Parent adverse origin
Child launch base
Child repair high / low
failed-repair origin
recent auction boundary
prior consumed checkpoint
prior high/low that still has unresolved role
```

A memory can change role after it is consumed or repaired.

`nearest memory` is never automatically TP, SL, or an entry veto.

When a memory is referenced, the rationale should state its **role**, not just its price.

---

## 9. Timeframe escalation state machine

This is a major cross-AI parity requirement.

### 9.1 Flat / no serious candidate

Default observation:

```text
H4/H1 context
advance one completed H1 at a time
```

Do not inspect every M15 simply because data is available.

### 9.2 Serious candidate begins

A serious candidate begins when H1 context makes an actual entry plausible and the trader needs local information.

Immediately change mode to:

```text
M15
```

From that point, reveal **only the next completed M15**, not the rest of the H1.

This prevents a common leakage/compliance failure:

```text
candidate exists at 17:59
-> accidentally reveal entire 18:00-18:59 H1
-> now the trader knows the move before deciding
```

If this occurs, the exposed interval is contaminated and no trade may be backfilled inside it.

### 9.3 Exact entry / falsification ambiguity

Use M5/M1 only when necessary to establish:

- exact entry reference;
- exact structural Hard SL price;
- first Hard SL touch;
- first destination touch;
- order of events inside an already revealed M15/H1;
- manual-exit ambiguity.

Do not stay permanently on M1 while flat. That creates noise authority and a different strategy.

### 9.4 Open Parent-Journey trade

Default:

```text
review every completed H1
```

At each H1 record campaign-health fields.

If a material warning appears, change to M15 until the warning is resolved or the position exits.

If the warning is clearly repaired, return to H1.

### 9.5 Open Local Bridge

Default:

```text
M15-centered lifecycle
```

Use exact M1 only for Hard SL/destination ordering and execution ambiguity.

---

## 10. Guarded advance for precommitted mechanical boundaries

A precommitted Hard SL is different from a discretionary future decision.

When an open position is being advanced to the next review cutoff, the helper should scan chronologically and stop immediately if a precommitted event occurs before the requested review time.

### 10.1 Parent-Journey example

Requested next review:

```text
current cutoff 10:59
next H1 review 11:59
Hard SL already frozen
```

Preferred helper behavior:

1. scan M1 chronologically from 11:00;
2. if Hard SL is first touched at 11:23, halt at 11:23;
3. report stop event and set causal cutoff to 11:23;
4. do **not** reveal 11:24-11:59 prices.

This is cleaner than revealing the whole H1 and later discovering the stop occurred inside it.

### 10.2 Local Bridge

If both Hard SL and fixed local destination exist, guard both chronologically.

Whichever event occurs in an earlier M1 row resolves first.

If both are touched inside the **same M1 bar**, exact intraminute ordering is unavailable.

Mark:

```text
INTRAMINUTE_EXECUTION_AMBIGUOUS
```

Do not invent tick order or claim exact execution P/L from M1.

---

## 11. Entry reference mechanics

Current replay convention:

- the discretionary decision is made only from already completed causal information;
- the descriptive entry reference is normally the **close of the latest fully revealed M1 at the decision cutoff**;
- no future next-bar open is used as if it were known;
- no intrabar best-price optimization is allowed after seeing the bar outcome.

Most serious decisions therefore occur at completed M15/H1 boundaries, with the final M1 close serving as the exact descriptive reference.

If a different already-revealed M1 reference is used, state why contemporaneously.

---

## 12. Hard SL mechanics

Before entry:

1. identify the current Child thesis;
2. identify the price that means the Child is no longer performing that thesis;
3. freeze that exact price;
4. compute initial risk from entry reference to that price.

Do not place SL because:

- a candle wick is conveniently nearby;
- a fixed ATR multiple says so;
- a round number looks clean;
- a desired R requires it.

The stop belongs to the Child's **functional falsification**.

Once frozen:

```text
touch = Child finished
never widen
later same-side move cannot rescue it
```

---

## 13. Good-pitch mechanism in this numeric workflow

The tooling protocol does not decide whether a pitch is good.

It forces the AI to make that judgment from a consistent input.

The current decision mechanism is:

```text
1. H1/H4: what larger route is actually progressing / repairing / failing?
2. Opposite case: what is the strongest live alternative?
3. M15: what exact Child is now attempting something?
4. What is new if this is a retry?
5. Does this Child have a real structural falsification?
6. Why is this Child worth risking on now, not merely independent?
7. What intended scale does the Child genuinely support?
8. Why this side and not the opposite?
9. Mirror + hidden-veto audit.
10. Only then TRADE / NO TRADE.
```

The decision is not made by any one pattern label.

---

## 14. Parent-Journey campaign-health mechanism

At every completed H1 for an open Parent-Journey position, read actual numeric evidence in this order:

```text
NEW FAVORABLE EXTREME?
H1 CLOSE / SETTLEMENT MIGRATION
COUNTERFLOW HIGH/LOW AND CLOSE SEQUENCE
DID DAMAGE GET REPAIRED?
DID COUNTERFLOW ESTABLISH STRONGER/LONGER BUSINESS?
WERE IMPORTANT ORIGINS / MEMORIES CONSUMED?
```

Then classify qualitatively:

```text
PROGRESSING
DAMAGED-BUT-REPAIRING
UNCLEAR
DETERIORATING
```

No fixed number of H1 bars is attached to those states.

### 14.1 Why the current method often waits through counterflow

A single adverse H1 does not automatically end a Parent trade if:

- a new favorable extreme was still produced;
- counterflow has not established durable adverse business;
- prior route remains repairable;
- important launch/origin structure is not being consumed.

### 14.2 Why the current method sometimes exits before Hard SL

A full manual exit becomes justified when actual progression ability materially deteriorates, e.g. a combination of:

- favorable extremes stop;
- settlement migrates persistently against the position;
- counterflow business becomes stronger/longer lived;
- damaged route does not repair;
- important route/origin/value is consumed.

This is not a hidden profit-lock multiple.

Manual exit reference is the latest revealed causal price at the decision time, not an optimized earlier intrabar price.

---

## 15. Local-Bridge mechanism

A Local Bridge is reviewed primarily on M15 because the thesis itself resolves locally.

The bridge has a declared destination/route before entry.

Do not upgrade it to a Parent trade merely because it becomes profitable.

If new Parent evidence forms while the bridge is open, any Parent participation requires a separate explicit trade decision under the full Parent-Journey audit.

---

## 16. Shadow indicators: exact calculation and authority

Indicators are derived only from **completed causal bars**.

They are not entry/exit authority.

### 16.1 H1 EMA9

Canonical implementation:

```text
EMA9 on completed H1 CLOSE
exponential weighting, span=9, adjust=False equivalent
```

### 16.2 H1 Stochastic(14,3,3)

Canonical implementation:

```text
rawK = 100 * (Close - rolling14 Low) / (rolling14 High - rolling14 Low)
K    = SMA3(rawK)
D    = SMA3(K)
```

Use only completed H1 bars.

### 16.3 H4 Wilder ATR14 and S

True Range:

```text
TR = max(
  High-Low,
  abs(High-prevClose),
  abs(Low-prevClose)
)
```

Wilder ATR14:

```text
initial ATR = mean(first 14 TR)
next ATR    = (previous ATR * 13 + current TR) / 14
```

For a decision at time `t`:

```text
S(t) = ATR14 of the previous fully completed H4 bar
```

`S` is a distance coordinate only.

Never turn it into a fixed SL/TP/entry threshold.

---

## 17. Standard optional image renderer, if another AI requires images

Numeric input remains mandatory.

If an AI also uses a chart image, use a fixed renderer so visual scale does not become a hidden strategy variable.

Minimum image standard:

- exact same causal prefix as numeric packet;
- no future candles;
- linear y-axis;
- no manual zoom/pan after seeing the candidate;
- fixed bar count per timeframe;
- y-range determined only from visible high/low plus fixed proportional padding;
- timestamp and price axes visible;
- no automatically drawn support/resistance/trendline;
- no indicator overlay unless explicitly marked shadow-only;
- no decision may cite `looks steep`, `looks stretched`, candle pixel size, or screen angle without numeric restatement.

Recommended fixed image windows, if used:

```text
H4: 20 bars
H1: 24 bars
M15: 16 bars
```

The image is a visualization of the canonical numeric packet, not a separate information source.

---

## 18. Standard textual output from the tooling layer

The deterministic tooling layer should output data, not trade opinions.

Example H1 packet:

```text
CUTOFF 2025-06-12 07:59
H1 COMPLETED
2025-06-12 04:00 O=... H=... L=... C=...
2025-06-12 05:00 O=... H=... L=... C=...
2025-06-12 06:00 O=... H=... L=... C=...
2025-06-12 07:00 O=... H=... L=... C=...

S(previous completed H4 ATR14)=...
H1 EMA9=...
H1 STOCH K=... D=...
```

The AI then applies the strategy and compliance harness to that packet.

Tool output must not contain labels such as:

```text
BUY
SELL
trend score
strong support
entry probability
```

Those would silently move discretionary strategy into tooling.

---

## 19. Tooling failure / contamination rules

### 19.1 Hash mismatch

If the M1 hash does not match authority:

```text
FAIL CLOSED
```

Do not continue the official replay on an unverified file.

### 19.2 Future reveal

If future prices are accidentally exposed:

- record exact exposed interval;
- do not insert a trade inside it;
- continue only from the end of the contaminated interval;
- preserve the incident in the session audit.

### 19.3 Candidate cadence violation

If a serious candidate should be on M15 but an entire H1 is accidentally revealed:

- record `COMPLIANCE/CADENCE INCIDENT`;
- no hindsight trade in the skipped M15 interval;
- resume from the revealed boundary.

### 19.4 Tool substitution

If the canonical numeric helper is unavailable, do not silently switch to an image-only workflow.

A substitute workflow must reproduce:

- exact raw-M1 causal prefix;
- same completed-bar aggregation;
- same timeframe escalation;
- same exact stop/destination chronology handling;
- same numeric decision packet.

Otherwise label the session `TOOLING NON-PARITY` and do not compare its discretionary results as equivalent execution.

---

## 20. Current June adoption boundary

This tooling protocol was formalized by explicit user instruction during the ongoing June 2025 replay.

At the moment of formalization, the causal replay state was:

```text
cutoff:   2025-06-12 07:59
position: J-025 LONG OPEN
entry:    3352.75
Hard SL:  3346.20
MFE:      3377.78 through current revealed prefix
status:   DAMAGED / DETERIORATING CANDIDATE
next mode: M15
```

No price after `2025-06-12 07:59` was used to design this protocol.

This is a **user-directed tooling-standardization amendment**, permitted by the June frozen-harness exception for explicit user instruction.

It does not change market-entry/exit strategy rules.

For research accounting, preserve:

```text
June pre-tooling-formalization segment: 2025-06-02 01:00 through 2025-06-12 07:59
June standardized-tooling segment:       after 2025-06-12 07:59
```

Do not pretend the tooling standard was prospectively documented before the first segment.

---

## 21. Cross-AI parity requirement

A future ChatGPT, Codex, or another AI session may have different internal capabilities.

For an execution to count as V9 tooling-parity, it must nevertheless use the same external observation contract:

```text
1. verified authoritative raw M1
2. monotonic causal prefix
3. raw-M1-derived completed H4/H1/M15
4. numeric OHLC as primary perceptual input
5. H1 default while flat
6. M15 only after serious-candidate escalation
7. H1 campaign review for Parent-Journey positions
8. M15 warning review
9. M1/M5 only for exact execution/falsification ambiguity
10. guarded stop/destination chronology
11. no image-only decision authority
12. same strategy + same compliance packet
```

If an AI cannot follow this contract, its replay should be labeled separately rather than merged into the same strategy-performance evidence.

---

## 22. One-line operational rule

> V9 is traded from a verified chronological raw-M1 prefix, reconstructed into completed numeric H4/H1/M15 context with explicit timeframe escalation; images are optional visualization only, while all discretionary Parent/Child/pitch/risk decisions must be auditable in exact causal price terms.
