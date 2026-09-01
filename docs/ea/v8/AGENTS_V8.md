# V8 Research Instructions

Status: `ACTIVE`
Generation: `V8`
Last synchronized: `2026-09-01`
Production authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## 1. Current branch map

```text
V8-A
FROZEN / CURRENT ABSOLUTE-$10 MOVEMENT CONTROL

V8-A2
RETAINED ABSOLUTE-$10 CHALLENGER / NOT PROMOTED
relative-rank reliability layer retained
TV79 research/shadow only

V8-A-N
RETAINED ATR-NORMALIZED MOVEMENT CHALLENGER / ACTIVE RESEARCH
no MT5 authority
next task = normalized fresh-high strategy architecture

V8-B
PAUSED / NEGATIVE-RESULT AUTHORITY

V8-C LONG
PROVISIONAL FROZEN / MT5 REAL-TICK VERIFIED
do not add entry filters

V8-C-S1 SHORT
RESEARCH-ONLY / M1 PROXY

FIXED-$10 FRESH75 AUTO-DIRECTION
DEVELOPMENT CONTROL / NO AUTHORITY
broad technical direction ceiling ~59%
1.30R fixed-dollar payoff = development comparison candidate only

NORMALIZED FRESH-HIGH STRATEGY
CURRENT PRIMARY RESEARCH
trigger -> direction -> ATR-consistent SL/TP must be developed as separate stages
```

## 2. Frozen V8-A

Do not change:

```text
P(reach C0 +/-$10 within 15m/30m/60m)
53 causal M1 features
2024 <- 2022-2023
2025 <- 2022-2024
2026 <- 2022-2025
```

V8-A remains the absolute-dollar control.

## 3. V8-A2

Retained research challenger:

```text
86 causal features
four-class <=15 / 15-30 / 30-60 / no-hit survival
full 60m purge
```

Outer AUC:

```text
          2024     2025     2026
P15     0.8660   0.8736   0.8190
P30     0.8501   0.8565   0.7999
P60     0.8130   0.8384   0.7925
```

Reliability state:

```text
R15/R30/R60 = current score percentile vs immediately prior 288 completed M5 scores
EXTREME = all >=90
HIGH = all >=75
QUIET = all <=25
```

None of A/A2 determines direction.

## 4. V8-A-N normalized challenger

V8-A-N changes the movement target scale, not direction.

Causal scale:

```text
ATR = pre-decision M5 Wilder ATR14
barrier = k * ATR
```

Prototype distances:

```text
0.75 / 1.00 / 1.25 / 1.50 / 1.75 / 2.00 / 2.50 / 3.00 ATR
```

Key structural evidence:

- fixed-$10 movement base rate changes by orders of magnitude across years;
- fixed ATR-multiple movement base rates are highly stable across 2022-2026;
- normalized future excursion quantiles are highly stable across years;
- normalized fresh-75 triggers have strong and stable realized movement precision.

Example `2ATR` all-M5 base rates:

```text
P15 18.41 / 18.77 / 18.61 / 18.50 / 18.19%
P30 40.57 / 40.00 / 40.04 / 40.13 / 39.20%
P60 66.81 / 64.91 / 65.13 / 66.38 / 65.63%
      2022    2023    2024    2025    2026
```

V8-A-N does not replace frozen A/A2.

Prototype separate-distance models have rare monotonicity violations. Final architecture must enforce:

```text
farther distance -> probability cannot increase
longer horizon -> probability cannot decrease
```

Do not deploy the current independent-distance coefficient packs.

Read `V8_A_N_ATR_NORMALIZED_MOVEMENT_RESEARCH_20260901.md`.

## 5. Current normalized fresh-high research contract

The next strategy is not "old fresh75 with ATR stops".

Research stages must remain separated:

### N1 trigger
Freeze one normalized fresh-high movement population first.

Candidate trigger family:

```text
previous P15(k ATR) <75%
current P15(k ATR) >=75%
```

Current candidates for structural comparison:

```text
k = 1.25 / 1.50 / 2.00 ATR
```

Selection at N1 must be outcome-blind with respect to LONG/SHORT P/L.

Use movement precision, count, year stability, clustering and implementation quality.

### N2 direction
Only after N1 is frozen, develop a direction engine on that exact population.

Do not automatically reuse the fixed-$10 fresh75 direction engine.

Do not mix direction discovery with trigger selection.

### N3 risk/payoff
Only after direction is frozen, test ATR-consistent SL/TP.

Do not choose SL/TP while changing direction.

### N4 comparison
Compare the complete normalized strategy against fixed-$10 controls.

## 6. Fixed-$10 fresh75 control

Existing trigger:

```text
previous fixed-$10 P15 <75%
current fixed-$10 P15 >=75%
mandatory LONG/SHORT
next M5 open
```

Broad ~790-feature technical tournament did not find a robust ~70% mandatory-direction rule.

2025/2026 are consumed for this branch.

Payoff development with fixed SL=$10:

```text
TP $10   -> 1.00R
TP $12   -> 1.20R
TP $12.5 -> 1.25R
TP $13   -> 1.30R
TP $13.5 -> 1.35R
```

Observed 1.20-1.35R positive plateau.

`$13 / 1.30R` is the central development comparison candidate because both 2025 and 2026 stayed above 52% WR with about +0.20R/trade.

This is not promotion authority and must not be fine-tuned further.

## 7. V8-C LONG

Frozen:

```text
M5 SMA20 contact-start
V8-A P15 > prior-288 Q75
Stoch K14>D3
completed M15 3-bar up
completed H1 3-bar down
=> LONG next M5 open
SL/TP +/-10
one position
```

Accepted R0.4:

```text
2024 N152 WR59.87% +29.26R
2025 N165 WR61.21% +37.35R
2026 N139 WR58.99% +25.24R
pooled N456 WR60.09% +91.85R
```

Do not modify entry.

V8-C exit/winner-continuation work remains a separate retained research track and must not contaminate normalized fresh-high research.

## 8. V8-C-S1

Research-only M1 proxy:

```text
N140 / WR58.57% / +24R
```

No MT5 authority.

## 9. Session/time

XM GOLD# timestamps use Cyprus/server DST interpretation unless execution evidence proves otherwise.

NY local 08:00-10:30 was the strongest recurring fixed-target movement window.

Session is context/prior and overlaps strongly with movement state. It is not an authorized hard filter.

For V8-A-N, session relationships must be remeasured rather than copied from fixed-$10 A2.

## 10. TradingView

TV79 and P15 probability candles remain research/shadow visualization layers.

Do not assume an ATR-normalized model trained on XM GOLD# transfers to a TradingView feed without separate feed/parity testing.

## 11. Permanent research rules

- no look-ahead;
- completed HTF bar only after its close;
- partial HTF only from already observed lower-TF data;
- current state excluded from its own trailing percentile;
- right-censored outcomes remain censored;
- discovery and validation separate;
- no threshold rescue after validation;
- keep movement trigger, direction engine and exit architecture separate;
- do not reuse variables across stages without a separate test;
- execution-environment changes are separate evidence;
- GOLD# 2021 remains locked.

## 12. Current work order

1. Preserve V8-A, V8-A2 and V8-C controls unchanged.
2. Freeze V8-A-N normalized fresh-high trigger family using structural movement evidence.
3. Develop direction engine on the frozen normalized trigger population.
4. Freeze direction before ATR-consistent SL/TP research.
5. Compare full normalized strategy with fixed-$10 1R and fixed-$10 1.30R controls.
6. Resume V8-C exit/S1 work separately when desired.
7. Keep GOLD# 2021 locked.

## 13. Reading authority

1. `HANDOFF_V8.md`
2. `V8_A_N_ATR_NORMALIZED_MOVEMENT_RESEARCH_20260901.md`
3. `V8_FRESH75_AUTODIRECTION_RESEARCH_20260901.md`
4. `V8_C_EXIT_PATH_RESEARCH_PLAN_20260901.md`
5. `DECISIONS_V8_RESEARCH_DIRECTION_ADDENDUM_20260901.md`
6. `RESEARCH_STATE_V8.md`
7. `BACKLOG_V8.md`
8. A2 / V8-C historical result docs as needed.

Always refresh GitHub HEAD before continuing.
