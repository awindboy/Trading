# V8 Research Instructions

Status: `ACTIVE`
Generation: `V8`
Active branches:
- `V8-A MOVEMENT PROBABILITY` — FROZEN / RETAINED / CURRENT MOVEMENT CONTROL
- `V8-A2 MOVEMENT CHALLENGER` — RESEARCH COMPLETE / RETAINED / NOT PROMOTED
- `V8-B LEARNED DIRECTION` — PAUSED / NEGATIVE-RESULT AUTHORITY
- `V8-C LONG ENTRY` — PROVISIONAL FROZEN / MT5 REAL-TICK VERIFIED ON OPEN DEVELOPMENT EVIDENCE
- `V8-C-S1 SHORT ENTRY` — ACTIVE RESEARCH / M1 PROXY ONLY
Production authority: `NONE`
Research EA authority: `V8MAMTFStochResearchEA R0.4` for LONG validation only
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## 1. Current thesis

V8-A remains the reliable direction-free movement-state control. Broad autonomous direction learning did not become stable enough for authority. The practical use of V8-A is therefore movement/environment estimation; direction may be supplied by deterministic event geometry or discretionary chart judgment.

V8-A2 research confirms that movement modeling can be improved modestly with better representation and target structure, but no challenger currently justifies replacing frozen V8-A.

## 2. Frozen V8-A contract

Do not change the current authority:

```text
C0 = completed causal decision price
barrier = +/-10 GOLD price units
H = 15m / 30m / 60m
53-feature causal M1 movement representation
walk-forward policy:
2024 <- 2022-2023
2025 <- 2022-2024
2026 <- 2022-2025
```

The current MT5 movement-probability indicator and coefficients remain unchanged.

## 3. V8-A2 challenger result

The first A2 tournament tested:

- explicit barrier-difficulty / volatility-regime features;
- unified multi-horizon first-hit-time / survival modeling;
- shallow nonlinear HGB;
- future-excursion distribution modeling;
- signless tick microstructure/activity;
- chronological blocked CV;
- selective 90% precision diagnostics;
- conformal abstention diagnostics;
- causal monthly refit/recalibration diagnostics.

The two repeatable positive clues were:

```text
original 53 features + 33 barrier-difficulty/regime features
multi-horizon survival / first-hit-time formulation
```

Strict 60m-purged survival challenger AUC:

```text
          2024     2025     2026
P15     0.8660   0.8736   0.8190
P30     0.8501   0.8565   0.7999
P60     0.8130   0.8384   0.7925
```

Frozen control AUC:

```text
          2024     2025     2026
P15     0.8566   0.8715   0.8177
P30     0.8418   0.8526   0.7977
P60     0.8068   0.8316   0.7868
```

Improvement is real but modest. A2 is research-only and has no MT5 authority.

Read `V8_A2_MOVEMENT_CHALLENGER_RESEARCH_20260901.md` for full results and audit notes.

## 4. 90% accuracy policy

Do not optimize raw classification accuracy. Movement prevalence changes dramatically by regime and can make NO-MOVE accuracy misleading.

Any 90% claim must report:

```text
precision / selective accuracy
coverage
calendar-year breakdown
future-block stability
base rate
```

Internal blocked CV may exceed 0.90 AUC without future-year AUC doing so. Random K-fold is not authority.

## 5. V8-A prospective reliability policy

The main live-model risk is calibration/base-rate drift rather than proven collapse of ranking skill.

For prospective use, monitor:

```text
AUC / ranking
Brier score
calibration by score bucket
P15/P30/P60 decile hit rates
high-score vs low-score ordering
recent 30/60/90d versus historical range
```

Do not auto-retrain because one short window is weak. Recalibration/refit is a separate controlled research change.

## 6. V8-B negative-result authority

Do not revive without materially new causal information:

- original B1 high-AUC model with HTF look-ahead;
- broad endpoint sign;
- local endpoint sign / slope / excursion dominance;
- micro-barrier mining;
- V8-A weighting or magnitude weighting;
- non-reproducible selective direction tails;
- simple WAIT/recenter endpoint confirmation.

The 15m exclusive-direction target remains only a weak clue, approximately 0.603 / 0.556 / 0.535 AUC in 2024/2025/2026.

## 7. V8-C LONG frozen research contract

```text
Market: GOLD#
Decision frame: M5
M5 SMA20 contact-start
P15 > prior-288 same-model-year Q75
raw Stochastic K14 > D3
latest completed M15 close > close 3 completed bars earlier
latest completed H1 close < close 3 completed bars earlier
=> LONG next M5 open / first real tick
TP = actual fill +10
SL = actual fill -10
one position only
```

Accepted R0.4 real-tick open-development evidence:

```text
2024 N152 WR59.87% +29.26R
2025 N165 WR61.21% +37.35R
2026 N139 WR58.99% +25.24R
pooled N456 WR60.09% +91.85R
expectancy +0.201R/trade
PF ~1.49
```

Do not add new LONG entry filters. Current +/-10 full exit validates entry edge only, not final exit architecture.

## 8. V8-C-S1 SHORT research

Research-only rule:

```text
M5 SMA20 contact-start
P15 > prior-288 Q75
raw Stochastic K < D
previous M5 high < previous SMA20
event M5 close < event SMA20
trailing 288 M5 net displacement < 0
=> SHORT
```

M1 one-position proxy:

```text
2024 N41 WR58.54%
2025 N51 WR54.90%
2026 N48 WR62.50%
pooled N140 WR58.57% +24R
```

No MT5 authority yet.

## 9. Permanent causality rules

Completed resampled bars are available only when:

```text
bar_start + timeframe_duration <= decision_time
```

Current partial HTF inputs may use only already-observed lower-timeframe data. Outcome windows crossing an evaluation boundary must be purged.

For a multi-horizon label using information through 60m, training eligibility is governed by the 60m resolution boundary even when reading a 15m/30m output.

Current P15 must never enter its own prior-288 threshold.

## 10. Research separation

Keep separate:

```text
movement-model quality
entry edge
winner continuation
exit architecture
execution
market suitability
portfolio/exposure
```

Do not modify frozen V8-A to rescue direction, entry or exit results.

## 11. Current next work

1. Preserve V8-A and V8-C LONG unchanged as controls.
2. Treat V8-A2 survival/regime models as research-only challengers.
3. Add prospective V8-A reliability logging before considering any A2 replacement.
4. Continue V8-C-S1 SHORT MT5 real-tick validation if the entry branch is resumed.
5. After entry freeze, continue winner-continuation / exit research.
6. Keep GOLD# 2021 locked.

## 12. Reading authority

Read next:

1. `docs/ea/v8/HANDOFF_V8.md`
2. `docs/ea/v8/V8_A2_MOVEMENT_CHALLENGER_RESEARCH_20260901.md`
3. `docs/ea/v8/V8_C_ENTRY_ARCHITECTURE_MT5_VALIDATION_20260901.md`
4. `docs/ea/v8/DECISIONS_V8_A2_ADDENDUM_20260901.md`
5. `docs/ea/v8/DECISIONS_V8_ADDENDUM_20260901.md`
6. `docs/ea/v8/RESEARCH_STATE_V8.md`
7. `docs/ea/v8/BACKLOG_V8.md`
8. legacy `docs/ea/v8/DECISIONS_V8.md`

`GOLD# 2021 = LOCKED / UNTOUCHED`
