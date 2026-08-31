# V8 Research State

Status: `ACTIVE / V8-A FROZEN + V8-C LONG PROVISIONAL FROZEN + V8-C-S1 SHORT RESEARCH`
Date: `2026-09-01`
Production authority: `NONE`
Market: `GOLD#`
Untouched reserve: `GOLD# 2021`

## V8-A

`FROZEN / POSITIVE OPEN-DEVELOPMENT MOVEMENT EVIDENCE`

Target:

```text
P(reach C0 +/-10 within 15m / 30m / 60m)
```

Walk-forward:

```text
2024 <- 2022-2023
2025 <- 2022-2024
2026 <- 2022-2025
```

Direction-free.

## V8-B

`PAUSED / NEGATIVE-RESULT AUTHORITY`

Important result:

Broad learned direction remained weak or unstable after strict causal reconstruction.

The original B1 positive result is invalidated by HTF look-ahead.

The best weak local clue, 15m exclusive direction, decayed approximately:

```text
0.603 / 0.556 / 0.535
```

No standalone direction-model deployment authority.

## V8-C LONG

`PROVISIONAL FROZEN / MT5 REAL-TICK VERIFIED ON OPEN DEVELOPMENT EVIDENCE`

Frozen entry:

```text
M5 SMA20 contact-start
P15 > prior-288 Q75
K14 > D3
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
expectancy +0.201R/trade
PF ~1.49
max observed closed-trade DD ~7.64R
```

No artificial EXPERT exits in accepted R0.4 runs.

## Runtime history

- R0/R0.1: iCustom deployment dependency fixed with embedded V8-A resource.
- R0.2: unnecessary host-period initialization hard-fail removed.
- R0.3: causal online P15 queue introduced; execution fail-close bug discovered.
- R0.4: actual protection-state verification fixed the execution bug.

R0.3 economics are invalid.

## Current SHORT candidate

Simple symmetric SHORT is rejected.

V8-C-S1:

```text
P15 > prior-288 Q75
K < D
previous M5 entirely below SMA20
event closes below SMA20 after contact-start
trailing 288 M5 net displacement < 0
=> SHORT
```

M1 proxy:

```text
2024 N41 WR58.54%
2025 N51 WR54.90%
2026 N48 WR62.50%
pooled N140 WR58.57% +24R
```

No MT5 authority yet.

## Exit status

Current +/-10 full exit validates entry edge only.

Average winner remains near 1R, so final exit architecture is not solved.

Holding-time compression:

```text
2024 ~279m
2025 ~56m
2026 ~15m
```

must be studied separately from entry quality.

## Immediate action

1. Keep V8-C LONG unchanged.
2. MT5 real-tick validate V8-C-S1 SHORT.
3. If SHORT survives, freeze entry architecture.
4. Move to winner-continuation / exit research.
5. Keep 2021 locked.
