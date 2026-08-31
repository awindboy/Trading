# V8 Research Instructions

Status: `ACTIVE`
Generation: `V8`
Active branches:
- `V8-A MOVEMENT PROBABILITY` — FROZEN / RETAINED
- `V8-B LEARNED DIRECTION` — PAUSED / NEGATIVE-RESULT AUTHORITY
- `V8-C LONG ENTRY` — PROVISIONAL FROZEN / MT5 REAL-TICK VERIFIED ON OPEN DEVELOPMENT EVIDENCE
- `V8-C-S1 SHORT ENTRY` — ACTIVE RESEARCH / M1 PROXY ONLY
Production authority: `NONE`
Research EA authority: `V8MAMTFStochResearchEA R0.4` for LONG validation only
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## 1. Current thesis

V8-A remains a frozen movement-probability control.

The most important current V8 result is that stable directional edge did not emerge from a broad standalone direction classifier, but a deterministic conditional LONG entry did emerge when a high V8-A movement state was combined with a specific causal M5 event and completed multi-timeframe path configuration.

Current interpretation:

> V8-A supplies movement/environment reliability. Direction becomes conditionally useful only inside a specific event geometry. LONG and SHORT are not assumed to be symmetric.

## 2. V8-A remains frozen

Do not change:

```text
C0 = completed causal decision price
barrier = +/-10 GOLD price units
H = 15m / 30m / 60m
53-feature causal M1 movement representation
walk-forward historical model policy:
2024 <- 2022-2023
2025 <- 2022-2024
2026 <- 2022-2025
```

V8-A is not LONG/SHORT authority.

## 3. V8-B is negative-result authority

Do not revive without a materially new causal formulation:

- original B1 high-AUC model;
- any M15/H1 bar-start look-ahead path;
- broad endpoint sign;
- local 5/10/15/30/60m endpoint sign;
- future local slope;
- excursion dominance;
- micro-barrier mining;
- V8-A-weighted direction training;
- future-magnitude weighting;
- non-reproducible selective direction tails;
- simple WAIT 1/3/5m -> recenter -> endpoint sign.

The 15m exclusive-direction target remains only a weak clue:

```text
2024 ~0.603
2025 ~0.556
2026 ~0.535
```

No standalone V8-B direction model has deployment authority.

## 4. V8-C LONG frozen research contract

```text
Market: GOLD#
Decision frame: M5

1. M5 SMA20 CONTACT START

2. V8-A P15 high relative movement state:
   current P15 >
   linear 75th percentile of the immediately prior 288 completed M5 P15 states,
   same V8-A model calendar year only

3. completed M5 raw Stochastic:
   K14 > D3
   D3 = SMA3(raw K)
   no additional slowing

4. latest completed M15:
   close > close 3 completed M15 bars earlier

5. latest completed H1:
   close < close 3 completed H1 bars earlier

=> LONG at exact next M5 open / first real tick

TP = actual fill +10.0
SL = actual fill -10.0
one position only
```

Do not add AO / RSI / MACD / session / 20-80 / extra Stochastic-slope filters to this frozen entry.

## 5. Accepted MT5 R0.4 real-tick evidence

Every Tick based on real ticks, GOLD#, M5:

```text
2024:
N 152
WR 59.87%
+29.26R
+0.193R/trade
PF 1.47
max closed-trade DD ~7.64R

2025:
N 165
WR 61.21%
+37.35R
+0.226R/trade
PF 1.57
max closed-trade DD ~5.10R

2026 through 2026-08-28:
N 139
WR 58.99%
+25.24R
+0.182R/trade
PF 1.43
max closed-trade DD ~5.10R

pooled:
N 456
WR 60.09%
+91.85R
+0.201R/trade
PF ~1.49
max loss streak 6
```

R0.4 has no artificial EXPERT immediate closes in the accepted runs.

Tester ledgers recorded commission/swap/fee as zero, so this is not universal full-cost authority for another execution environment.

## 6. Current SHORT research

The simple mirror SHORT is rejected:

```text
P15 > Q75
K < D
M15 down
H1 up
```

Approximate open-development WR:

```text
2024 42.07%
2025 48.76%
2026 49.07%
pooled 46.51%
```

The current separate SHORT candidate is V8-C-S1:

```text
M5 SMA20 contact-start
P15 > prior-288 Q75
raw Stochastic K < D
previous M5 high < previous SMA20
event M5 close < event SMA20
trailing 288 M5 net displacement < 0
=> SHORT next M5 open
TP -10 / SL +10
```

M1 one-position research proxy:

```text
2024 N41 WR 58.54%
2025 N51 WR 54.90%
2026 N48 WR 62.50%
pooled N140 WR 58.57%
+24R
+0.171R/trade
```

This SHORT rule is not MT5 authority yet.

## 7. Permanent causality rules

Completed resampled bars are available only when:

```text
bar_start + timeframe_duration <= decision_time
```

Current partial HTF inputs are allowed only if rebuilt from already-observed lower-timeframe data.

Outcome windows crossing an evaluation boundary must be purged from training.

Current P15 must never enter its own prior-288 Q75 threshold.

## 8. Research separation rules

Keep separate:

```text
entry edge
winner continuation
exit architecture
execution
market suitability
portfolio / exposure
```

The current +/-10 full exit validates entry edge only.

Do not interpret its ~1.01R average winner as final exit authority.

## 9. Current next work

1. Preserve V8-C LONG R0.4 semantics unchanged as control.
2. Implement V8-C-S1 SHORT only as a research variant.
3. MT5 Every Tick real-tick validate SHORT separately for 2024/2025/2026.
4. Audit parity and execution before combined P/L.
5. If SHORT survives, freeze entry architecture.
6. Then move to winner continuation / exit architecture.
7. Seek average winner meaningfully >1R without sacrificing realized WR >=50%.
8. Treat broker/account/server/feed/commission changes as separate execution environments.
9. Keep GOLD# 2021 locked.

## 10. Reading authority

Read next:

1. `docs/ea/v8/HANDOFF_V8.md`
2. `docs/ea/v8/V8_C_ENTRY_ARCHITECTURE_MT5_VALIDATION_20260901.md`
3. `docs/ea/v8/DECISIONS_V8_ADDENDUM_20260901.md`
4. `docs/ea/v8/RESEARCH_STATE_V8.md`
5. legacy `docs/ea/v8/DECISIONS_V8.md`
6. `docs/ea/v8/BACKLOG_V8.md`

`GOLD# 2021 = LOCKED / UNTOUCHED`
