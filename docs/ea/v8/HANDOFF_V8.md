# V8 Development Handoff

Last updated: `2026-09-01`
Current phase: `V8-C DETERMINISTIC ENTRY ARCHITECTURE / SHORT VALIDATION + EXIT PREPARATION`
Production authority: `NONE`
Research EA authority: `V8MAMTFStochResearchEA R0.4` for frozen LONG validation
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## 1. Current branch status

### V8-A

`FROZEN / RETAINED`

V8-A remains the 15m/30m/60m +/-10 movement-probability model and MT5 shadow indicator.

Historical walk-forward policy:

```text
2024 <- 2022-2023
2025 <- 2022-2024
2026 <- 2022-2025
```

Do not change V8-A to improve direction or entry statistics.

### V8-B

`PAUSED / NEGATIVE-RESULT AUTHORITY`

Important failures remain authoritative:

- original B1 invalidated by M15/H1 look-ahead;
- non-reproducible selective direction tail rejected;
- broad and ultra-local endpoint sign stayed near chance;
- independent up/down touch models mostly relearned movement intensity;
- micro barriers did not stabilize direction;
- V8-A weighting did not create direction;
- WAIT/recenter endpoint confirmation failed.

The 15m exclusive-direction target was the best weak clue but decayed approximately 0.603 -> 0.556 -> 0.535 AUC and has no deployment authority.

### V8-C LONG

`PROVISIONAL FROZEN ENTRY CANDIDATE / MT5 REAL-TICK VERIFIED ON OPEN DEVELOPMENT EVIDENCE`

Frozen contract:

```text
M5 SMA20 contact-start
P15 > prior-288 same-model-year Q75
raw Stoch K14 > D3
completed M15 close > close 3 bars ago
completed H1 close < close 3 bars ago
=> LONG next M5 open
SL = fill -10
TP = fill +10
one position
```

No symmetric SHORT is part of this contract.

## 2. How the current LONG emerged

The research did not jump directly to the final rule.

Useful intermediate findings:

### Stochastic A1

```text
2024 N132 WR 59.85% +26R
2025 N223 WR 56.95% +31R
2026 N192 WR 56.77% +26R
pooled N547 WR 57.59% +83R
```

### P15 50-cross armed Stochastic

```text
N1086
WR 52.49%
+54R
```

### AO replacement

Failed:

```text
N1086
WR 48.53%
-32R
```

On AO/Stochastic disagreement, Stochastic won approximately 55.97% versus AO 44.03%.

This is why AO was not added to V8-C LONG.

## 3. V8-C LONG robustness findings

Removing P15 relative state degraded later years:

```text
58.84 / 54.21 / 51.74
```

Using the same directional state without MA20 event context:

```text
56.46 / 53.13 / 49.42
```

Using all MA20-contact bars rather than contact-start:

```text
55.77 / 52.35 / 52.51
```

Entry delay degraded the edge, especially +5m in 2026.

P15 Q60/Q67/Q70/Q75/Q80 and windows 144/288/576 showed a broad robust relationship. Q75/288 was retained as a neutral stable point rather than a single-year optimum.

Adding extra Stochastic slope gave only a marginal WR increase while reducing trade count, so it was rejected from the frozen entry.

## 4. MT5 implementation corrections

### R0 / R0.1

External V8-A iCustom dependency could fail OnInit. V8-A EX5 was embedded as a resource.

### R0.2

Hard `_Period == M5` initialization failure was removed. The strategy explicitly requests M5/M15/H1 data.

### R0.3

P15/Q75 was changed to an online causal prior-state queue.

R0.3 then revealed an execution bug: `PositionModify()` false was treated as protection failure, producing 74 artificial near-zero-second EXPERT closes in the first 2024-2025 run.

R0.3 economics are invalid.

### R0.4

Protection is now verified from actual `POSITION_SL`/`POSITION_TP`, and a position is fail-closed only if exact protection genuinely cannot be established.

Accepted R0.4 runs contain zero artificial EXPERT exits.

## 5. Accepted R0.4 real-tick results

```text
2024:
N 152
WR 59.87%
+29.26R
+0.193R/trade
PF 1.47
maxDD ~7.64R
max loss streak 6
median hold ~279.4m

2025:
N 165
WR 61.21%
+37.35R
+0.226R/trade
PF 1.57
maxDD ~5.10R
max loss streak 5
median hold ~55.8m

2026 through 2026-08-28:
N 139
WR 58.99%
+25.24R
+0.182R/trade
PF 1.43
maxDD ~5.10R
max loss streak 5
median hold ~15.1m
```

Pooled:

```text
N 456
274 wins / 182 losses
WR 60.09%
+91.85R
+0.201R/trade
PF ~1.49
max observed closed-trade DD ~7.64R
max loss streak 6
```

2026 parity is especially useful:

```text
authorized 142
blocked by existing position 3
actual trades 139
```

The actual one-position count matched the prior 2026 M1 proxy count of 139.

## 6. Important execution caveat

Tester ledgers show:

```text
commission = 0
swap = 0
fee = 0
```

Therefore this is not universal full-cost authority for another broker/account/server/feed.

Average winner is only about +1.01R and average loser about -1.02R.

The current full exit at 1R is an entry-edge test architecture, not the final strategy.

## 7. Why holding time changed

Median holding time fell:

```text
2024 ~279m
2025 ~56m
2026 ~15m
```

The fixed 10-dollar GOLD barrier represents a smaller relative move as GOLD price/volatility rise.

Do not confuse stable entry WR with stable exit economics.

## 8. SHORT history

The simple mirror SHORT failed:

```text
P15 > Q75
K < D
M15 down
H1 up
```

Approximate WR:

```text
2024 42.07%
2025 48.76%
2026 49.07%
pooled 46.51%
```

Interpretation: LONG and SHORT are not symmetric. The mirror often shorts a short-term drop inside a broader positive path.

## 9. Current SHORT candidate — V8-C-S1

Research-only rule:

```text
M5 SMA20 contact-start
P15 > prior-288 Q75
raw Stoch K < D
previous M5 high < previous SMA20
event M5 close < event SMA20
trailing 288 M5 net displacement < 0
=> SHORT next M5 open
SL +10 / TP -10
```

M1 one-position proxy:

```text
2024 N41 WR 58.54%
2025 N51 WR 54.90%
2026 N48 WR 62.50%
pooled N140 WR 58.57%
+24R
+0.171R/trade
```

Combined LONG+SHORT M1 proxy was approximately:

```text
N574
WR 60.98%
+126R
```

This is not MT5 validation and not untouched evidence.

## 10. Immediate next task

Do not add more LONG entry filters.

Next:

```text
preserve R0.4 LONG control
+ implement V8-C-S1 SHORT research variant
+ MT5 real-tick 2024/2025/2026
+ report SHORT separately
+ audit execution/parity
```

If SHORT survives, freeze the entry architecture.

Then move to:

```text
winner continuation
partial realization
runner architecture
2R/3R opportunity
dynamic exit
```

The target is to retain realized WR >=50% while making average winner meaningfully greater than 1R.

## 11. Reserve

GOLD# 2021 remains locked.

Do not open 2021 while entry/exit architecture is still changing.

## 12. Reading order next session

1. `docs/ea/v8/AGENTS_V8.md`
2. `docs/ea/v8/HANDOFF_V8.md`
3. `docs/ea/v8/V8_C_ENTRY_ARCHITECTURE_MT5_VALIDATION_20260901.md`
4. `docs/ea/v8/DECISIONS_V8_ADDENDUM_20260901.md`
5. `docs/ea/v8/RESEARCH_STATE_V8.md`
6. legacy `docs/ea/v8/DECISIONS_V8.md`
7. `docs/ea/v8/BACKLOG_V8.md`

Always refresh GitHub HEAD before continuing.
