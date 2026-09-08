# V10 Research State

Date: `2026-09-08`
Status: `ACTIVE / INITIAL GEMINI CAUSAL REPLAY STARTED`
Market: `GOLD# ONLY`
Replay period: `2025-01 ONLY`
Production authority: `NONE`
EA authority: `NONE`

## Purpose

V10 is an isolated experiment measuring whether Gemini can perform analysis and discretionary decisions comparable to V9 when it receives only causally available GOLD# data and a clean V9-derived behavior contract.

V10 does not modify or extend V9 research state.

## Pipeline status

- Independent runner: `scripts/v10_gemini_jan2025.py`
- Behavior contract: `V10_GEMINI_BEHAVIOR_CONTRACT.md`
- Output root: `output/v10_gemini_jan2025/`
- Source SHA256 verified: `626d81d3d6ba94ac80d00748fa83e11ff5ec90df7fb6c98688c77f20d1604ff2`
- Causal packet tests: `6 PASS`
- V9 January decisions, outcomes, and checkpoint notes are excluded from Gemini context.

## Causal replay performance optimization

The local packet builder was optimized without changing Gemini's system instruction,
prompt construction, chart dimensions, visible bars, model settings, or review cadence.

```text
first cutoff in a run:
full source SHA256 verification + causal cache initialization

later cutoff in the same run:
validate immutable source metadata/header
seek to the saved byte offset
read only newly revealed M1 rows
update bounded D1/H4/H1/M15/M5/M1 rolling bars

same-cutoff retry:
reuse the causal market cache and existing chart PNGs
```

Safety behavior:

- The cache is monotonic and refuses a cutoff earlier than its saved causal boundary.
- The exact requested M1 cutoff row must exist; no rounding is allowed.
- A source size or modification-time change triggers a full SHA256 recheck and fails closed on mismatch.
- Cache initialization still performs the authoritative full SHA256 verification once per run.
- Timing and cache/render actions are recorded in every packet and decision artifact.

Measured local packet preparation on the current machine:

```text
2025-01-02 12:00 initial cache + charts: 10,846.77 ms internal
                                            11.50 s wall
2025-01-02 12:15 incremental + charts:         494.56 ms internal
                                             1.12 s wall
2025-01-02 12:15 same-cutoff retry:              16.77 ms internal
                                             0.68 s wall
```

Equivalence evidence:

- At `12:00`, revealed-row count, all three PNG SHA256 values, prompt SHA256, and contract SHA256 match the pre-optimization Flash packet exactly.
- At `12:15`, revealed-row count and all three PNG SHA256 values match the pre-optimization Flash Lite packet exactly.
- At `12:30`, revealed-row count and all three PNG SHA256 values match the pre-optimization Flash packet exactly.
- Unit coverage verifies that incrementally maintained timeframe bars equal a full source rescan and that source mutation is rejected.

The approximately `0.44-0.60 s` chart render is not the dominant delay. A changed cutoff still receives newly rendered, byte-identical chart construction; chart reuse is limited to an exact-cutoff retry. Gemini API inference remains the dominant per-decision latency and was not altered because changing its inputs or thinking settings could change analysis quality.

## Active run

```text
runId: v10_jan2025_gemini_001
model: gemini-3.5-flash-lite
thinking: high
current cutoff: 2025-01-02 12:30
state: FLAT / prior child resolved
next model-requested review: +60 minutes
```

## First causal sequence

### 2025-01-02 12:00

```text
ARMED
NOT_YET
LONG observational direction
next review: 15 minutes
```

Gemini considered the parent and child route bullish but waited for local repair evidence.

### 2025-01-02 12:15

```text
TRADEABLE
ENTER_LONG
entry reference: 2638.41 current M1 close
falsification anchor: 2631.09
destination: 2639.87, then 2645
next review: 15 minutes
```

### 2025-01-02 12:30

```text
RESOLVED
EXIT
exit reference: 2644.43 current M1 close
observed high: 2646.29
next review: 60 minutes
```

Descriptive price change:

```text
2644.43 - 2638.41 = +6.02 points
```

This is not execution-valid P/L.

## Initial process audit

Positive:

- The model used Parent Journey, child route, active memory, anchor, destination, and `NOT_YET` language coherently.
- It waited at 12:00, requested a tighter checkpoint, entered later, and resolved at its stated destination.
- It did not receive any V9 January answer or future row.

Concern:

- Entry reference to anchor distance was approximately `7.32` points.
- Room to the first stated destination `2639.87` was only approximately `1.46` points.
- Room to `2645` was approximately `6.59` points.
- Therefore the claimed attractive structural asymmetry was not supported by the model's own selected geometry, even though the trade outcome was positive.
- The response used `genuineRestorationBehavior` partly as entry confirmation rather than clearly stating future invalidation behavior.

Interpretation:

```text
positive outcome
!=
V9-quality attempt proven
```

The first sequence shows that Gemini can imitate much of the V9 vocabulary and lifecycle, but semantic consistency must be evaluated separately from realized direction/outcome.

Do not repair or relabel this frozen sequence after seeing the result.

## Next task

Continue the same frozen run from:

```text
2025-01-02 12:30
FLAT
next causal cutoff: 2025-01-02 13:30
```

Keep the current behavior contract unchanged for this run so its evidence remains internally consistent.

---

## Gemini 3.5 Flash high comparison run

```text
runId: v10_jan2025_gemini35flash_001
model: gemini-3.5-flash
thinking: high
temperature: 0.0
contract: unchanged
start cutoff: 2025-01-02 12:00
resolved cutoff: 2025-01-03 05:00
```

### Decision chronology

```text
2025-01-02 12:00  ARMED / NOT_YET / LONG bias
2025-01-02 12:30  ENTER_LONG at current close ~2644.43
2025-01-02 13:00  HOLD
2025-01-02 13:30  HOLD
2025-01-02 14:00  HOLD
2025-01-02 15:00  HOLD
2025-01-02 16:00  HOLD
2025-01-02 17:00  HOLD
2025-01-02 18:00  HOLD
2025-01-02 19:00  HOLD
2025-01-02 19:30  HOLD
2025-01-02 20:00  HOLD
2025-01-02 20:30  HOLD
2025-01-02 21:00  HOLD
2025-01-02 22:00  HOLD
2025-01-03 01:00  HOLD
2025-01-03 04:00  HOLD
2025-01-03 05:00  EXIT / destination resolved
```

Frozen trade thesis:

```text
entry reference: 2644.43
falsification anchor: 2638.05
invalidation: sustained M5/M15 close below 2638.05
destination: 2663.40 H4 memory
planned risk: ~6.38 points
planned reward: ~18.97 points
planned geometry: ~2.97R
```

Observed lifecycle:

- Price briefly wicked to approximately `2636.00`, but Gemini retained the position because its frozen invalidation required sustained M5/M15 acceptance below `2638.05`, not a wick.
- The anchor, invalidation behavior, destination, and Parent Journey description remained stable throughout the open trade.
- The destination was first reached during the 2025-01-03 04:15 M15 bar with a high around `2664.05`.
- The next scheduled review was 05:00, where Gemini returned `EXIT`.
- The 05:00 current M1 close was approximately `2661.94`.

Descriptive captured result at the decision checkpoint:

```text
2661.94 - 2644.43 = +17.51 points
+17.51 / 6.38 = approximately +2.74R
```

This is not exact execution P/L.

### Initial comparison with Flash Lite

Flash Lite:

```text
entered earlier at ~2638.41
used 2631.09 anchor
resolved at ~2644.43
captured ~+6.02 points
geometry from its own stated levels was weaker than claimed
```

Flash:

```text
waited until 12:30
entered at ~2644.43 after local breakout confirmation
used a new 2638.05 breakout-base anchor
kept the 2663.40 destination unchanged
captured ~+17.51 points / ~+2.74R descriptively
```

On this single sequence, Flash showed materially better internal consistency with the V9 Decision Corridor principle than Flash Lite. This is one diagnostic trade and is not sufficient to establish model superiority.

### API use

```text
calls: 18
prompt tokens: 141,203
total tokens: 188,970
```

The large call count reflects model-selected 30/60/180-minute management checkpoints during one open trade.

---

## Second completed Flash trade

The optimized runner continued the same frozen Flash run after the first trade
resolved. No V9 answer or later market row was supplied.

```text
2025-01-03 06:00  NOT_YET
2025-01-03 07:00  NOT_YET
2025-01-03 08:00  ENTER_LONG at current M1 close 2659.49
2025-01-03 09:00  HOLD
2025-01-03 10:00  EXIT / structural invalidation
```

Frozen second-trade thesis:

```text
entry reference: 2659.49
falsification anchor: 2655.85
invalidation: sustained H1 close below 2655.85
destination: 2692.90
initial anchor distance: 3.64 points
```

Observed lifecycle:

- The maximum post-entry high was `2660.29` at `08:57`, approximately `+0.80` points from the entry reference.
- The 09:00 H1 candle closed at `2654.20`, below the frozen `2655.85` anchor.
- Gemini returned `EXIT` at the 10:00 review immediately after that H1 close became available.
- The 10:00 current M1 close was `2654.43`.
- The minimum post-entry low before that decision was `2651.89` at `09:23`.

Descriptive result at the decision checkpoint:

```text
2654.43 - 2659.49 = -5.06 points
-5.06 / 3.64 = approximately -1.39R
```

This is not exact execution P/L. The anchor represented a structural H1-close
condition rather than a broker hard stop, so intra-hour excursion and exit price
can exceed `-1R`.

Process interpretation:

- Gemini did not chase the 2663 resistance immediately after the first exit; it waited two reviews for a pullback.
- It preserved the entry anchor, H1-close invalidation behavior, and destination throughout the trade.
- It held at 09:00 because the frozen H1-close invalidation had not yet become available.
- The second trade lost, but its exit followed the predeclared structural condition rather than hindsight relabeling.

Continuation API and timing evidence:

```text
accepted calls: 5
prompt tokens: 39,208
total tokens: 58,206
accepted-call API time: 95.36 s
local preparation time: 12.03 s
```

The local total includes a one-time `10.21 s` cache initialization because the
first trade predated the optimization. Later new-cutoff market updates took
approximately `45-49 ms`; changed-cutoff chart rendering took approximately
`0.41-0.42 s`. The exact 08:00 retry reused both cache and charts and required
approximately `16.9 ms` locally.

Two 08:00 attempts on API key slot 1 received HTTP 429 before any decision was
accepted. State remained frozen at 07:00. The identical 08:00 packet then
succeeded with configured API key slot 2; this changed credentials only, not the
model, thinking level, contract, prompt, charts, or cutoff.
