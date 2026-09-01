# V8 Development Handoff

Last updated: `2026-09-01`
Current phase: `V8-C LONG EXIT/PATH AUDIT PREPARATION + FRESH75 SECONDARY DIRECTION RESEARCH`
Production authority: `NONE`
Research EA authority: `V8MAMTFStochResearchEA R0.4` for frozen V8-C LONG only
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## 1. Primary vs secondary track

Primary: `V8-C LONG exit / winner continuation`. Entry is provisionally frozen and real-tick verified; next question is whether +1R winners continue enough, with tolerable retracement, to create average winner meaningfully above 1R.

Secondary: `Fresh-P15-75 auto-direction`. Broad technical-indicator mining did not reach ~70% mandatory-direction accuracy. Tick-microstructure/new-information-source research may continue, but 2026 is already consumed development evidence for this branch.

Do not merge these tracks.

## 2. Movement layer

V8-A remains frozen. V8-A2 remains a research challenger. A2 relative state uses prior-288 R15/R30/R60 and EXTREME/HIGH/QUIET definitions. TV79 is a separate TradingView 79-feature price-only fallback, not FULL A2. Higher-TF P15 candles aggregate completed M5 P15 values only and are visualization-only.

## 3. Session finding

XM GOLD# timestamps are handled as Cyprus/server time with DST. The strongest recurring movement cluster was NY local 08:00-10:30. Session and A2 rank overlap strongly; EXTREME should not be rejected merely because it occurs outside NY. No session hard filter is authorized for V8-C LONG.

## 4. V8-C LONG authority

```text
M5 SMA20 contact-start
P15 > prior-288 Q75
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
+0.201R/trade, PF ~1.49
```

Do not tune LONG entry. Current +1R full exit is only an entry-edge validator.

## 5. Current primary task — exit/path audit

Reconstruct all 456 accepted LONG paths. Do not inspect only the 274 current winners.

Measure:

- MFE/MAE;
- time to +0.5R/+1R;
- post-1R +1.25/+1.5/+2/+3R continuation;
- post-1R retracement before extension;
- continuation time;
- censoring;
- year stability.

Do not infer spike/reversal from shorter holding time; fixed $10 scaling changed materially.

Exit evidence order:

```text
2024 discovery
freeze simple exit family
2025 validation 1
2026 validation 2
2021 locked
```

Initial family: +1R control; 50%@1R + 50%@1.5R; 50%@1R + 50%@2R; partial +1R then BE; simple fixed trailing after +1R. Only later test conditional V8-A/A2/session continuation.

Goal: WR >=50%, average winner meaningfully >1R, positive full-cost expectancy, stable validation.

## 6. V8-C-S1

Still M1-proxy only: N140, WR58.57%, +24R. No MT5 authority. Resume separately and do not alter LONG.

## 7. Fresh75 status

Trigger remains previous P15<75 and current P15>=75, next-M5-open mandatory LONG/SHORT. Entering every high-P15 bar is rejected. Roughly 790 causal technical/MTF/candle/activity features were explored; no robust ~70% all-trigger direction solution. Best compact development result remained about 59%.

Evidence status correction: 2025 and 2026 are consumed for this branch. Any earlier tick-probe wording calling 2026 untouched is superseded.

If this branch resumes, prefer genuinely new information sources over more indicator threshold mining.

## 8. Immediate next session

1. Refresh GitHub HEAD.
2. Read `AGENTS_V8.md`.
3. Read `V8_C_EXIT_PATH_RESEARCH_PLAN_20260901.md`.
4. Recover exact accepted R0.4 trade timestamps/fills.
5. Build a shadow path ledger without changing entry/exits.
6. Inspect 2024 continuation first.
7. Freeze exit family before opening 2025/2026 continuation.
8. Keep 2021 locked.
