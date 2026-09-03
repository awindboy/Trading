# V8 Development Handoff

Last updated: `2026-09-03`
Current phase: `GOLD EXECUTABLE MAPPING REVALIDATED -> EARLY-PATH ACTION / EXPOSURE BRIDGE`
Production authority: `NONE`
Market: `GOLD# ONLY`
Open development evidence: `2022-2026`
Untouched reserve: `GOLD# 2021`
Source Git HEAD verified before this synchronization: `636524efc0335b1569405cfed420e84549a0c4b9`

## 1. Immediate instruction to the next session

The chronological replay and the executable-mapping revalidation have already been completed.

Do **not** repeat old ledger archaeology or re-run old P0/P2 count reconciliation unless there is a new direct contradiction.

Read first:

1. `V8_EXECUTABLE_MAPPING_REVALIDATION_20260903.md`
2. `DECISIONS_V8_EXECUTABLE_MAPPING_ADDENDUM_20260903.md`

The immediate next question is:

> Can the causal information already available during the first 1-10 minutes after ACCEPTANCE be converted into better entry/reduction/abort/add/hold decisions without destroying trade frequency or repurposing structural labels as direction labels?

This is GOLD-only.

## 2. Hard GOLD-only scope

The user explicitly froze all other markets until GOLD is complete.

Therefore:

- no USDJPY# research;
- no XAUEUR# research;
- no BTCUSD# research;
- no market-universe transfer;
- no source-of-move external branch;
- no GOLD# 2021.

Old external-market documents remain historical/preregistered context only.

## 3. P0/P2 correction

P0/P2 are alternate deterministic **training de-overlap realizations**, not execution phases.

The trained model is inferred over the full modelable M5 population.

Current P0 fresh75 events occur across all `m5_index % 5` residues. The prior statement that P0 replay traded only one-fifth of M5 decisions was incorrect.

Do not merge P0/P2 trades. P2 remains robustness evidence.

## 4. Current P0 funnel authority

```text
P0 full-M5 inference

2024:
fresh75 653
touch15 510
reveal 426
25% pullback fill 390
ACCEPTANCE 279

2025:
fresh75 535
touch15 420
reveal 361
25% pullback fill 318
ACCEPTANCE 236

2026:
fresh75 321
touch15 244
reveal 211
25% pullback fill 193
ACCEPTANCE 153

TOTAL:
fresh75 1509
touch15 1174
reveal 998
25% pullback fill 901
ACCEPTANCE 668
```

Rates:

- fresh75 -> +/-0.25S touch within 15m: `77.8%`.
- reveal -> 25% pullback fill: `90.3%`.
- fill -> ACCEPTANCE: `74.1%`.

316/668 ACCEPTANCE events (`47.3%`) had pullback and reclaim within the same M1. Do not discard these by convenience. M1 ambiguity ultimately requires real-tick MT5 confirmation.

Current P2 ACCEPTANCE robustness population:

```text
2024 316
2025 235
2026 144
total 695
```

## 5. What the good prediction results actually mean economically

### Movement onset

P15/fresh75 remains a real movement-onset mechanism. The 77.8% touch15 rate supports that semantics.

It does not supply direction.

### Pullback/reclaim

The 25% pullback -> ACCEPTANCE transition is high, but direct trading is weak:

Blind symmetric pullback trade, 901 fills with spread:

```text
WR 48.1%
mean -0.039R
PF 0.925
```

Directly trading the reclaim:

```text
WR 67.8%
mean +0.028R
PF 1.339
average winner only about +0.162R
```

Therefore ACCEPTANCE is a useful state transition, not a finished payoff architecture.

### Structural retention

Actual future retention is highly associated with Base outcome:

```text
15m retained:
N224
Base WR 86.2%

not retained:
N444
Base WR 29.5%
```

But the acceptance-time `micro3` retention ranking does not become a profitable Base filter automatically.

Representative high-micro3 direct Base mapping:

```text
2025+2026 combined
N90
WR 44.4%
mean -0.111R
PF 0.800
```

Therefore preserve micro3 as structural-quality prior only.

### Winner continuation

Realized progress after the market has already demonstrated strength remains the strongest executable mechanism.

P0 High-Q runner:

```text
N61
WR 49.18%
mean about +0.287R
PF about 1.68-1.71
average winner about +1.4R
positive mean R in each year
```

P2 robustness:

```text
N70
WR about 51.4%
mean about +0.214R
PF about 1.53-1.56
```

This is still sparse development evidence, not production authority.

## 6. Frozen Base and account replay result

Routine Base control:

```text
ACCEPTANCE
-> next M1 open
-> +0.25S TP
-> -0.25S SL
```

Current P0 668:

```text
WR 48.5%
mean about -0.029R
PF about 0.944
```

Chronological `$1,000` wrapper:

```text
Base P/L       -$31.85
Runner P/L    +$250.21
Net           +$218.36
End balance   $1218.36
Floating MDD  -21.85%
Max overlap   2
```

Runner-only 60m control:

```text
End balance   about $1220.89
Net           about +$220.89
Floating MDD  about -9.86%
```

Interpretation:

The wrapper's profit came from the runner, not from routine Base. Paying at every ACCEPTANCE is not justified merely as an information probe.

## 7. Current architecture semantics

```text
ONSET
P15 fresh75
= movement opportunity

-> M1-close reveal
-> pullback
-> reclaim = ACCEPTANCE

ACCEPTANCE QUALITY
micro3 structural-quality prior

DYNAMIC STRUCTURAL STATE
PRISTINE / DAMAGED / CLOSE_BROKEN

EARLY REALIZED PATH
causal progress + hazard updates

WINNER CONTINUATION
close intact + realized progress

EXECUTABLE LAYER
entry / reduce / abort / add / hold / exit / size
```

Never collapse the layer semantics.

## 8. Current failed direct mappings

Do not rescue these by threshold tuning without a new mechanism:

- blind 25% pullback symmetric trade;
- routine ACCEPTANCE Base;
- high micro3 as direct Base permission;
- structural-extreme stop mapping as a direct micro3 rescue;
- unconditional `CLOSE_BROKEN -> immediate exit`;
- simple t10 standalone runner entry as a year-stable final rule.

The t10 progress target itself has very high discrimination for future High-Q, but the standalone t10 trading mapping was negative in 2025. Preserve the target evidence; do not promote the action rule.

## 9. Mandatory reporting format from now on

If a future report says:

```text
AUC = X
```

it must also say, if tested:

```text
target = ?
known at = ?
action rule = ?
N = ?
WR = ?
mean R = ?
PF = ?
avg winner/loss = ?
year split = ?
status = ?
```

If no executable mapping exists:

`NO EXECUTABLE TRADING RESULT YET`.

## 10. Immediate next research: Base economic bridge

Keep current Base untouched as control.

Build shadow-only checkpoints:

```text
t0 = ACCEPTANCE
t1 = +1m
t3 = +3m
t5 = +5m
t10 = +10m
```

At each checkpoint:

- use only information causally known by then;
- include only events/trades still unresolved at that checkpoint;
- ask whether existing structural/path information discriminates **subsequent executable economics**, not merely retention;
- quantify N, WR, mean R, PF and year stability;
- compare P0 and P2 as robustness realizations, not merged trades;
- no new generic indicators initially;
- no future MFE15 used as earlier permission;
- no threshold rescue after validation reversal.

Only if a causal checkpoint survives should an executable challenger be preregistered, for example:

- delayed entry;
- small/zero initial exposure then confirmation;
- early risk reduction/abort;
- later add;
- hold/exit change.

Do not change execution first and rationalize it later.

## 11. Final strategy constraints remain

A final strategy still needs:

- realized WR >=50%;
- average winner/payoff meaningfully >1R;
- clearly positive spread/commission/slippage-adjusted expectancy;
- acceptable drawdown/loss streak;
- robustness across independent GOLD periods before 2021 reserve is touched;
- no artificial all-trades-at-1R flattening just to satisfy WR.

## 12. Reading order

1. `AGENTS_V8.md`
2. this file
3. `V8_EXECUTABLE_MAPPING_REVALIDATION_20260903.md`
4. `DECISIONS_V8_EXECUTABLE_MAPPING_ADDENDUM_20260903.md`
5. `DECISIONS_V8_RESEARCH_INFERENCE_GUARDRAILS_ADDENDUM_20260903.md`
6. `V8_SEQUENTIAL_CAPITAL_ALLOCATION_RESEARCH_20260903.md`
7. `V8_A_N_SLOW_PRACTICAL_MOVEMENT_CHARACTERIZATION_20260903.md`
8. `V8_A_N_SLOW_DYNAMIC_STRUCTURAL_STATE_RESEARCH_20260903.md`
9. `V8_A_N_SLOW_PERSISTENCE_RETENTION_RESEARCH_20260902.md`
10. `V8_DIRECTIONAL_ECONOMIC_VIABILITY_FALSIFICATION_20260903.md`
11. older V8 research history only when needed.

Always refresh GitHub HEAD before continuing.
