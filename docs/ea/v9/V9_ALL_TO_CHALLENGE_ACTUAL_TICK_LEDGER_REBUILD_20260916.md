# V9 ALL_TO_CHALLENGE Actual-Tick Ledger Rebuild and Literal Oracle Correction

Date: `2026-09-16`
Status: `CONSUMED-DATA SHADOW RESEARCH / NOT STRATEGY AUTHORITY`
Market: `GOLD# ONLY`
Base GitHub HEAD: `f57e10c670666dd763152e6302d0952f9a7a2f5d`

## 1. Purpose

This checkpoint freezes the research ledger used after the user reran the terminal study with:

```text
unlimited accepted Children
each Child keeps its own structural Hard SL
all surviving Children remain open
route CHALLENGED -> close all surviving Children together
```

This is a **terminal-research comparator only**. It does not replace the frozen role-based prototype authority.

Uploaded tester evidence:

```text
V9_R0_events(1).csv
SHA256 f6b9189ed80afe6fa4f606dc06eff98beeef85b241429a2499d1532524c61293

V9_R0_trades(1).csv
SHA256 ef0cab9a00e67b1b02a12541c0e496dd619a4e9e76ec1401021ac965ad840dad
```

The tester INIT record explicitly reports:

```text
execute=true
management=ALL_TO_CHALLENGE
bootstrap_era=false
bootstrap_levels=false
```

Trade roles in this ledger are `INDEPENDENT_CHILD`.

## 2. Raw tester BASE

Full uploaded closed-trade ledger:

```text
700 closed Children
PnL +6,973.87
PF 1.532826
WR 41.00%
DD 1,700.62
Avg win +69.90
Avg loss -31.69
P90 +95.055
P95 +136.929
Max winner +588.90
```

Exit reasons:

```text
CHALLENGE_OPENS                         474
STRUCTURAL_SL                           168
TICK_COLLISION_STOP_CHALLENGE_OPENS      58
```

There are `194` resolved routes in the uploaded closed ledger.

## 3. Comparable H4-covered cohort

The supplied H4 source ends at source bar `2026-08-28 20:00`.
That bar becomes causally known at tester finalization on `2026-08-31 01:00:02`.

To avoid inventing H4 HA state beyond available source coverage, BASE / ORACLE / candidate comparison uses:

```text
191 resolved routes
693 closed Children
```

Only `7` of the raw `700` closed Children are excluded from H4-based comparisons.

Comparable BASE:

```text
N 693
PnL +7,210.31
PF 1.565510
WR 41.2698%
DD 1,700.62
Avg win +69.7916
Avg loss -31.3270
P90 +94.95
P95 +137.132
Max +588.90
```

## 4. Causal H4 HA mapping

H4 source rows are source-bucket starts.

For research decisions:

```text
nominal_end = source H4 bar start + 4h
known_at = first tester H4_FINALIZED tick at or after nominal_end
```

This preserves weekend / market-gap chronology.

Standard Heikin-Ashi:

```text
HA_CLOSE = (O + H + L + C) / 4
first HA_OPEN = (O + C) / 2
later HA_OPEN = (previous HA_OPEN + previous HA_CLOSE) / 2
```

Hypothetical HA exits use the tester's executable quote at `H4_FINALIZED`:

```text
LONG close -> logged Bid
SHORT close -> logged Ask
```

A Child whose own structural SL / BASE exit occurred earlier remains dead and is never resurrected.

## 5. Literal oracle correction

The literal answer sheet is:

```text
TRUE LAST ACCEPTED CHILD
-> first completed opposite-color H4 HA after that Child
-> close every still-open Child at that finalized H4 executable quote
```

During NHA reconstruction one route showed:

```text
opposite-color HA1
-> NHA continues same opposite color
-> final accepted Child occurs inside that NHA episode
-> next completed opposite-color HA is the literal oracle
```

Therefore the prior implementation that required the oracle bar itself to be a color-transition HA1 missed one route.

Correct current answer sheet:

```text
157 Oracle routes
```

The exceptional non-transition oracle route is `route_id=100`, oracle time `2025-03-05 20:00:00`.

Literal Oracle on the common 693-Child cohort:

```text
PnL +19,827.81
PF 3.617619
WR 53.3911%
DD 856.81
Avg win +74.0610
Avg loss -23.4512
P90 +121.852
P95 +179.162
Max +588.90
```

Hence:

```text
BASE -> ORACLE improvement = +12,617.50
```

The earlier `156` transition-HA1 oracle remains useful as historical evidence but is superseded for the current literal answer sheet.

## 6. Research populations

Literal Oracle route count by first-entry year:

```text
2024 58
2025 58
2026 41
TOTAL 157
```

For 2025-2026:

```text
99 literal Oracle routes
```

Of those, `43` have a repeat-HA1 state with prior opposite-HA history and therefore have causal `CycleMin` available at the oracle event.

## 7. Result files

Current result folder:

`docs/ea/v9/results/terminal_state_table_20260916/`

Primary ledgers:

- `BASE_FULL_700_TRADES.csv`
- `BASE_COMMON_693_TRADES.csv`
- `ORACLE_LITERAL_COMMON_693_TRADES.csv`
- `ORACLE_LITERAL_ROUTE_ANSWER_SHEET_157.csv`
- `HA1_STATE_EVENTS.csv`
- `NHA_CAUSAL_STATE_EVENTS.csv`

All later 2026-09-16 terminal-state studies must use this corrected literal oracle unless a later checkpoint explicitly supersedes it.

## 8. Authority status

No strategy authority changes.

The frozen prototype remains governed by `V9_PROTOTYPE_AUTHORITY_20260914.md`.
The `ALL_TO_CHALLENGE` comparator and literal terminal oracle are research-only evidence.
