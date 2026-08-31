# V8 Decisions Addendum — 2026-09-01

This file continues `DECISIONS_V8.md` without rewriting the legacy decision history.

## D-V8-051 — Pause broad standalone learned-direction mining

Date: `2026-09-01`

Decision:

Pause V8-B broad/local standalone direction-model mining as the active path.

Reason:

After strict causal reconstruction, endpoint sign, local slope, excursion dominance, micro barriers, V8-A weighting, magnitude weighting and WAIT/recenter endpoint confirmation did not produce stable strong sign information.

The negative results remain authority and should prevent repeating the same research under new model names.

---

## D-V8-052 — Promote deterministic event-conditioned direction to the active V8 path

Date: `2026-09-01`

Decision:

The active V8 direction research path is V8-C: deterministic conditional entry built from factual event geometry, frozen V8-A movement state and completed causal multi-timeframe path information.

Reason:

This formulation produced materially more stable later-year directional expectancy than broad learned direction.

---

## D-V8-053 — Freeze the exact V8-C LONG entry contract

Date: `2026-09-01`

Decision:

Freeze:

```text
M5 SMA20 contact-start
P15 > prior-288 same-model-year Q75
raw Stochastic K14 > D3
completed M15 close > close 3 bars earlier
completed H1 close < close 3 bars earlier
LONG next M5 open
SL/TP +/-10 from actual fill
one position
```

Do not add entry filters while adjacent hypotheses are tested.

Reason:

Ablations showed that the V8-A relative state, MA20 contact-start event and multi-timeframe configuration all contribute. Additional slope/indicator filters did not provide enough robust incremental value.

---

## D-V8-054 — Interpret V8-A as environment/movement gate, not direction

Date: `2026-09-01`

Decision:

In V8-C, P15 > prior-288 Q75 is an environment / movement-reliability gate only.

Reason:

Removing the gate degraded later-year performance, but V8-A itself is direction-free and broad sign models remain weak.

---

## D-V8-055 — Reject AO as a replacement for Stochastic direction

Date: `2026-09-01`

Decision:

Do not replace V8-C Stochastic direction with AO color.

Reason:

On the tested schedule AO produced approximately 48.53% WR and -32R versus positive Stochastic behavior. On AO/Stochastic disagreement, Stochastic materially outperformed AO.

---

## D-V8-056 — Reject the symmetric SHORT mirror

Date: `2026-09-01`

Decision:

Reject:

```text
P15 > Q75
K < D
M15 down
H1 up
=> SHORT
```

Reason:

It produced approximately:

```text
2024 42.07%
2025 48.76%
2026 49.07%
pooled 46.51%
```

The failure indicates that LONG and SHORT are not causal mirrors.

---

## D-V8-057 — Runtime fixes R0 through R0.4 are implementation corrections, not strategy changes

Date: `2026-09-01`

Decision:

Classify the R0/R0.1 indicator-resource fix, R0.2 host-period fix, R0.3 online P15 queue, and R0.4 protection-state verification as runtime/parity corrections.

Reason:

None change the frozen entry signal semantics.

---

## D-V8-058 — Invalidate R0.3 economics due artificial expert closes

Date: `2026-09-01`

Decision:

Do not use R0.3 P/L as strategy evidence.

Reason:

The first R0.3 run contained 74 artificial near-zero-second EXPERT closes caused by incorrectly treating `PositionModify()` false as proof that exact SL/TP protection had failed.

---

## D-V8-059 — Accept R0.4 as the current LONG real-tick research authority

Date: `2026-09-01`

Decision:

Use the accepted R0.4 real-tick runs as current V8-C LONG research authority:

```text
2024 N152 WR59.87% +29.26R
2025 N165 WR61.21% +37.35R
2026 N139 WR58.99% +25.24R
pooled N456 WR60.09% +91.85R
expectancy +0.201R/trade
PF ~1.49
```

Reason:

The strategy population reproduces closely from research proxy to MT5, execution protection is correct, and no artificial EXPERT closes remain.

This is still open/consumed development evidence, not production authority.

---

## D-V8-060 — Treat the current +/-10 full exit as entry-edge validation only

Date: `2026-09-01`

Decision:

Do not promote the current 1R full-exit structure as the final exit architecture.

Reason:

Average winner is only around +1.01R. The project requires average winner/payoff to be meaningfully greater than 1R while preserving realized WR >=50% and positive cost-adjusted expectancy.

---

## D-V8-061 — Open a separate asymmetric SHORT candidate

Date: `2026-09-01`

Decision:

Open V8-C-S1 as research-only:

```text
M5 SMA20 contact-start
P15 > prior-288 Q75
raw Stochastic K < D
previous M5 high < previous SMA20
event M5 close < event SMA20
trailing 288 M5 net displacement < 0
=> SHORT
```

Reason:

The rule represents a different causal geometry: negative broader path plus MA20 resistance re-contact/failure. It is not a mirror of the LONG rule.

M1 one-position proxy:

```text
2024 N41 WR58.54%
2025 N51 WR54.90%
2026 N48 WR62.50%
pooled N140 WR58.57% +24R
```

No MT5 authority yet.

---

## D-V8-062 — Preserve LONG while validating SHORT

Date: `2026-09-01`

Decision:

Any SHORT implementation must be a research variant that preserves V8-C LONG semantics unchanged.

Reason:

Changing LONG and adding SHORT simultaneously would make attribution impossible.

---

## D-V8-063 — Freeze entry before beginning exit optimization

Date: `2026-09-01`

Decision:

If V8-C-S1 survives MT5 real-tick validation, freeze the entry architecture before winner-continuation / exit research.

Reason:

Entry survival and exit architecture are separate research questions. Entry filters must not be tuned to rescue later exit results.

---

## D-V8-064 — Fixed 10-dollar barrier requires separate regime-aware exit study

Date: `2026-09-01`

Decision:

Treat the observed holding-time compression as an exit/execution research issue:

```text
2024 median ~279m
2025 median ~56m
2026 median ~15m
```

Reason:

A fixed 10-dollar GOLD move changes relative scale as price level and volatility evolve.

This does not authorize changing V8-A's frozen movement target or the current entry-validation barrier.

---

## D-V8-065 — Keep GOLD# 2021 locked

Date: `2026-09-01`

Decision:

Do not open GOLD# 2021 while SHORT and exit architecture are still changing.

Reason:

2022-2026 are already consumed development evidence. The untouched reserve should not be spent on an architecture that is still being modified.
