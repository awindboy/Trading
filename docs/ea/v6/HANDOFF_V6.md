# V6 Development Handoff

Last updated: `2026-08-28`  
Current phase: `V6-002 PRECISION-PRESERVING STATE-ROUTED ARCHITECTURE RESEARCH`  
Current promoted candidate: `NONE`  
Current research benchmarks: `R2 primary / R2P alternate`  
Production authority: `NONE`

## Mandatory startup

1. Check latest GitHub HEAD.
2. Read root `AGENTS.md`.
3. Read root `docs/ea/HANDOFF.md`.
4. Read `AGENTS_V6.md`.
5. Read this file.
6. Read `RESEARCH_STATE_V6.md`.
7. Read `V6_001C_STATE_ROUTED_MECHANISM_RESULTS.md`.
8. Read `V6_002_R3_PRECISION_PRESERVING_H_STATE_CONTRACT.md`.
9. Read `DECISIONS_V6.md` and `BACKLOG_V6.md`.
10. Inspect exact code/data before execution.

GitHub wins over chat memory.

## Current user-level direction

V6 research must follow:

```text
indicator/state measurement
-> verify that it meaningfully describes market state
-> apply that state to strategy mechanism selection
-> replay raw market data and generate new trades
-> compare V3 vs V6 economics
```

Do NOT revert to:

```text
match indicator values to old V3 trade outcomes
-> rank by AUC/score
-> select the best filter
```

AI/ML is not an active route unless the user explicitly reopens it.

## Completed V6-001B/001C chain

### Indicator/state exploration

The initial conventional H1/H4 atlas did not reveal a standalone universal filter. Broader exploratory work then examined multiple timeframes/settings/combinations. The useful result was not a winning score but interpretable state coordinates.

Important constructs:

```text
M5 DMI5  = local directional pressure
H4 ADX14 = intermediate maturity/strength state
D1 ATR14 = background movement scale
```

### R1

`ADX>=25 + DMI aligned -> H`, `ADX>=25 + DMI opposed -> L`, weak ADX -> no trade.

Result:

```text
41 trades
WR 29.27%
avg+ 2.604R
EV +0.055R
DD 16.5R
2023/2024 negative
SHORT EV -0.638R
```

R1 is closed.

M5 DMI was redundant with the broad-event M5 transition in about 90% of events.

### R2

Recursive falsification reversed the H4 interpretation:

```text
ADX<25 -> H
ADX>=25 -> L
```

GOLD 2023-2025:

```text
75 trades
WR 41.33%
avg+ 2.924R
EV +0.622R
2023/24/25 all positive
LONG/SHORT both positive
DD 10R
```

Classification:

```text
MEANINGFUL DEVELOPMENT BENCHMARK
FINAL WR TARGET NOT YET MET
NO PRODUCTION AUTHORITY
```

### R2P

Existing H +2R/50% protection reused without tuning:

```text
75 trades
WR 44.0%
avg+ 2.300R
EV +0.452R
DD 8.5R
```

R2P is an alternate payoff benchmark.

## GOLD 2022 historical comparison

2022 is consumed; this is not pristine V6 validation.

```text
V3:
24 trades / WR 25.0% / avg+ 1.458R / EV -0.385R / total -9.25R / DD 10.25R

R2:
40 trades / WR 35.0% / avg+ 2.428R / EV +0.200R / total +7.987R / DD 6.75R

R2P:
40 trades / WR 37.5% / avg+ 1.966R / EV +0.112R / total +4.487R / DD 7.5R
```

R2 did not collapse like V3, but its 2022 profit was concentrated in Q4.

Module decomposition:

```text
R2 H: 2023-25 EV +0.704R -> 2022 EV +0.538R
R2 L: 2023-25 EV +0.293R -> 2022 EV -0.429R
```

H is the surviving clue. The simple inverse `ADX>=25 -> L` relation is not supported.

## Cross-market comparison

Same unmodified rules were replayed on full 2023-2025 XAUEUR/USDJPY/BTCUSD data.

```text
XAUEUR:
V3 -0.247R
R2 -0.353R
R2P -0.284R

USDJPY:
V3 -0.135R
R2 -0.017R
R2P -0.108R

BTCUSD:
V3 +0.090R
R2 -0.334R
R2P -0.310R
```

Therefore R2 improves GOLD period robustness but is not a universal market architecture.

BTC is especially important: V3 local precision remained weakly positive while broad R2 routing destroyed it. This motivates the active V6-002 principle:

> preserve V3 local precision and use state to change destination/authorization instead of replacing precision wholesale.

## Exact next task — R3

Read `V6_002_R3_PRECISION_PRESERVING_H_STATE_CONTRACT.md`.

R3 asks:

> Among H opportunities that already satisfy the V3 precision substrate, does H4 maturity distinguish when the H large-payoff destination remains healthy?

Do not change Candidate-A, direct-transfer, pullback geometry, H payoff, or L semantics in the first R3 shadow audit.

R3 first uses development data only. Only after the frozen shadow criterion is evaluated may a controlled strategy variant be constructed.

## Required R3 comparison panel

If R3 strategy construction is authorized, run the same frozen rule on:

```text
GOLD 2023-2025
GOLD 2022 consumed historical stress comparison
XAUEUR 2023-2025
USDJPY 2023-2025
BTCUSD 2023-2025
```

No market-specific threshold or payoff rescue.

## Evaluation rule

Always report jointly:

```text
N
WR
avg positive R
avg negative R
EV/trade
total R
DD
loss streak
year split
direction split
H/L contribution
winner concentration
```

The final goal remains WR>=50%, avg positive NET R>=2R and positive cost-adjusted EV, but a research candidate is not discarded solely because WR has not yet reached 50%.

## Research after R3

Priority:

1. H maturity / remaining-capacity mechanism;
2. L-specific correction-completion state — not inverse H;
3. outcome-blind market-suitability screen and frozen market universe;
4. mechanism-linked external/source-of-move context if internal state is insufficient;
5. exact execution/economics only after architecture stabilizes.

## Hard restrictions

- no AUC-driven promotion;
- no old-trade classification as the main V6 task;
- no parameter rescue on consumed outcomes;
- no market-specific threshold tuning;
- no automatic H variable -> L variable reuse;
- no production EA change yet;
- no GOLD 2021.
