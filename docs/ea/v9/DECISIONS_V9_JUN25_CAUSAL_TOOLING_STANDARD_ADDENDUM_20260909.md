# V9 Decisions Addendum — June 2025 Causal Tooling Standardization

Date: `2026-09-09`
Status: `ACTIVE DECISION / TOOLING AUTHORITY`
Scope: `USER-DIRECTED MID-JUNE TOOLING STANDARDIZATION`
Market: `GOLD# ONLY`

## D1. Why this amendment exists

The user identified a cross-AI execution problem:

> different AI sessions can read the same strategy while using materially different perceptual tools, such as numeric OHLC reconstruction versus visually scaled candlestick images.

Accepted conclusion:

```text
strategy parity
requires more than document parity
```

V9 now distinguishes three layers:

```text
STRATEGY AUTHORITY
COMPLIANCE HARNESS
TOOLING / OBSERVATION PROTOCOL
```

The third layer is standardized by:

`V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260909.md`

---

## D2. Numeric causal representation is canonical

Official V9 discretionary replay uses:

- authoritative raw M1 as data authority;
- exact chronological prefix control;
- raw-M1-derived completed H4/H1/M15;
- numeric OHLC as the primary perceptual representation;
- H1/M15 close/settlement sequences, highs/lows, repair/departure, and retained active memories as the observable evidence.

Chart images are optional visualization only and have no independent trade authority.

This decision is intended to reduce cross-model variation caused by chart zoom, y-axis scaling, visible-bar count, rendering style, and image perception.

---

## D3. Timeframe escalation is part of tooling parity

Official review state machine:

```text
FLAT / NO CANDIDATE
-> H1 default, H4 context

SERIOUS CANDIDATE
-> M15

EXACT ENTRY / SL / DESTINATION AMBIGUITY
-> M5/M1 only as needed

OPEN PARENT-JOURNEY
-> every completed H1
-> M15 on material warning

OPEN LOCAL BRIDGE
-> M15-centered
```

Once a serious candidate exists, revealing the rest of the H1 instead of the next M15 is a compliance/cadence incident.

No hindsight trade may be inserted into the exposed interval.

---

## D4. Guarded advance is preferred for precommitted events

For an open trade, Hard SL and declared Local-Bridge destination are already frozen mechanical boundaries.

The causal helper should scan M1 chronologically toward the next review cutoff and halt at the first precommitted event.

This prevents the AI from unnecessarily seeing prices after a trade was already mechanically resolved.

If stop and destination are both touched within the same M1 row, mark execution ambiguous. Do not invent intraminute ordering.

---

## D5. Do not preload future prices

Official helper behavior is streaming/prefix-based.

Do not use full-future-dataframe loading as the standard official replay path.

The helper may inspect the next row timestamp to determine whether it belongs behind the requested cutoff, but should not read future OHLC values when the timestamp is beyond the cutoff.

---

## D6. Indicators remain deterministic shadow outputs

For parity:

- H1 EMA9 uses completed H1 closes and `span=9, adjust=False` equivalent weighting;
- H1 Stochastic uses `(14,3,3)` with raw 14-period %K, then SMA3 K, SMA3 D;
- H4 `S` uses previous fully completed Wilder ATR14.

They remain shadow-only and receive no new trading authority.

---

## D7. Image use is subordinate

An AI may render a chart image only if:

- it uses exactly the same causal prefix;
- the canonical numeric packet is also available;
- no decision relies on image-only slope, candle pixel size, zoom, or visual stretch;
- any material visual claim is restated numerically.

If an AI cannot operate on the canonical numeric packet and instead relies primarily on an image, mark the replay:

`TOOLING NON-PARITY`.

Do not merge it with official V9 tooling-parity evidence.

---

## D8. June causal adoption boundary

This amendment was explicitly requested by the user while June replay was already in progress.

Freeze the adoption boundary at:

```text
cutoff: 2025-06-12 07:59
position: J-025 LONG OPEN
entry: 3352.75
Hard SL: 3346.20
MFE through boundary: 3377.78
campaign state: DAMAGED / DETERIORATING CANDIDATE
next observation mode: M15
```

No post-boundary June price may be used to design this tooling protocol.

This is permitted under the frozen-harness exception because the user explicitly changed the research contract.

It is primarily a **representation/tooling standardization**, not a market-rule revision.

For month-end research, distinguish pre-formalization and post-formalization segments.

---

## D9. No new market thresholds are introduced

This amendment does **not** define:

- minimum number of candles;
- minimum hold count;
- fixed display-derived trend angle;
- fixed move size;
- minimum R;
- fixed Parent classifier;
- candlestick-pattern entry rules;
- image-based overextension rules.

The purpose is to standardize what evidence the AI sees and when it sees it, not to pre-decide what that evidence must mean.
