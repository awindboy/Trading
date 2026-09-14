# V9 Development Handoff

Last updated: `2026-09-15`
Status: `PROTOTYPE FROZEN / ACTUAL-TICK VALIDATED / TERMINAL-ORACLE REPLICATION SHADOW RESEARCH NEXT`
Production authority: `NONE`
EA authority: `RESEARCH / DEMO ONLY`

## 1. Resume point

Do not return to broad entry-feature mining.
Do not change the current prototype because of consumed-data terminal research.

There are two lanes:

```text
A. execution lane
frozen BASE prototype -> EA R1 -> forward demo

B. strategy-research lane
oracle terminal-HA ledger -> causal replication -> actual-tick validation if earned
```

The user's immediate research priority is lane B.

## 2. Frozen BASE prototype

- H1/H4 causal 2-left / 2-right liquidity.
- Tick-native H4 Arrival chronology.
- PRIMARY_ACTIVE / CHALLENGED Grammar.
- Nearest active opposite H1 structural Hard SL.
- Previous-completed H4 Wilder ATR180.
- `ERA_RISK <= 4` eligibility.
- First accepted Child = ANCHOR; current exit `CHALLENGE_OPENS` unless own SL first.
- Later accepted Child = CONTINUATION; current exit next H4-liquidity Arrival unless own SL first.
- No fixed TP, SHORT ban, Child-count cap, session/day/hour filter, or duration timeout.

Actual-tick execution remains higher authority than M1 for execution chronology/fills.

## 3. Terminal research answer sheet

The research answer sheet is deliberately non-causal:

```text
TRUE LAST ACCEPTED CHILD
-> first opposite-color completed H4 HA (HA1)
-> close every still-open Child in that route
```

Full deterministic M1 population:

| Ledger | N | PnL | PF | WR | DD |
|---|---:|---:|---:|---:|---:|
| BASE | 1,139 | +8,530.74 | 2.023 | 65.58% | 440.35 |
| ORACLE terminal HA1 all-open | 1,139 | **+13,863.22** | **3.475** | **70.41%** | **288.75** |

Available full-history oracle improvement: `+5,332.48`.

The oracle is an answer sheet only. `TRUE LAST CHILD` must never become a feature or live rule.

## 4. Critical change in evaluation

From this checkpoint forward, **BASE-beating is not the primary success criterion**.

For any evaluation period `P`:

```text
Oracle recovery(P)
= (Candidate PnL(P) - BASE PnL(P))
  / (ORACLE PnL(P) - BASE PnL(P))
```

Compare all three ledgers on the same period.

Primary diagnostics:

1. Oracle improvement recovery.
2. Remaining oracle PnL gap.
3. Exact/same-HA oracle exit matches.
4. EARLY interventions before oracle terminal HA.
5. LATE exits and giveback versus oracle.
6. MISSED oracle exits.
7. Route/Child oracle regret.
8. Right-tail preservation.
9. PF/DD gap to oracle.

AUC and raw BASE delta are secondary.

## 5. Latest exploratory causal result

A broad screen tested HA morphology and persistence, H1/H4 HA context, H4 liquidity geometry, H1/H4 range/location indicators, RSI, MACD, DMI/ADX, EMA, Bollinger, Donchian, Ichimoku, movement-capacity context, and fixed Logistic/Tree/HGB models.

Important findings:

- HA morphology alone is not a strong terminal classifier; HA is more useful as a reversal event.
- H4 liquidity geometry remains the most repeatedly useful structural family.
- H1/H4 location measures contain additional information, but common single-indicator rules are generally too noisy as exits.
- Fixed duration since Child is weak; terminal stage is not a simple timeout.
- Complex ML did not show stable economic superiority over simple mechanical combinations on the same variables.

The most interesting current research candidate uses the first opposite H4 HA plus a high-precision mechanical combination of:

```text
Child-relative opposite-H4-liquidity pressure
+
H4 Donchian primary-location loss
+
opposite HA body strength / ATR180
```

On the 2024-2026 slice:

| Ledger | PnL |
|---|---:|
| BASE | +7,428.37 |
| current mechanical candidate | +7,869.42 |
| same-period ORACLE | **+11,625.62** |

Therefore:

```text
candidate BASE improvement       = +441.05
available same-period oracle gain = +4,197.25
oracle improvement recovery      = 10.51%
remaining oracle gap              = 3,756.20
```

The candidate selected `12` route events, with `0` answer-sheet early events; `9` route deltas were positive and `3` unchanged.

This is only a proof of concept. The important fact is not that it beats BASE; it is that **it still leaves about 89.5% of the same-period oracle improvement unrecovered**.

## 6. Timing discovery

The last Child need not be recognized at its entry instant.
Oracle delay screen:

| Activation delay after true last Child | PnL | PF |
|---|---:|---:|
| BASE | +8,530.74 | 2.023 |
| 0 H4 | +13,863.22 | 3.475 |
| 1 H4 | +13,839.03 | 3.464 |
| 2 H4 | +13,715.95 | 3.407 |
| 3 H4 | +13,471.13 | 3.272 |
| 4 H4 | +12,608.38 | 2.927 |

This means causal evidence gathered after the last accepted Child but before terminal HA can still reproduce much of the answer sheet.

## 7. Next session — exact research goal

The next session must ask:

> Why does the oracle earn the remaining gain that the current causal detector misses, and which part of that gain is causally recoverable without creating destructive early exits?

Required first work:

- build route-by-route and Child-by-Child **Oracle Gain Attribution**;
- partition oracle gain into `MATCH / EARLY / LATE / MISS` for every causal candidate;
- rank missed routes by oracle-regret contribution rather than by classification error count;
- inspect the largest unrecovered oracle-gain routes causally and reconstruct H4/H1 chart states;
- distinguish missing information from overly conservative operating points;
- test HA + liquidity + location/structure combinations mechanically first;
- compare ML only on exactly the same available variables/timestamps;
- use route-relative changes and depletion/replenishment states before adding arbitrary global thresholds;
- evaluate sequentially against the same-period oracle ledger after every experiment.

Do not optimize for a particular arbitrary recovery percentage. The objective is to maximize causally recoverable oracle value while preserving the right tail and keeping early-regret low.

## 8. Research philosophy for this lane

The goal is not to predict the literal final top or to manufacture certainty.
The target is to identify a state in which the next opposite HA deserves route-level profit-protection authority.

Current working decomposition:

```text
LIQUIDITY / STRUCTURE
-> where is the route in its participation life cycle?

LOCATION / DEPLETION
-> has primary-side delivery space/quality materially deteriorated?

HEIKIN-ASHI
-> has actual H4 momentum reversal now appeared?
```

## 9. Execution lane

`V9_NEXT_RESEARCH_CONTRACT_FORWARD_DEMO_20260914.md` remains valid for the unchanged BASE prototype.
Terminal-stage shadow research must not silently alter EA R1 semantics.
