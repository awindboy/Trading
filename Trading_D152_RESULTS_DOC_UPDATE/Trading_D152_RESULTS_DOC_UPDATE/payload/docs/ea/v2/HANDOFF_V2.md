# V2 Development Handoff

Last updated: 2026-08-22  
Repository state before this documentation update: `7cb26133235c45a3756492af951900f15213f8cb`  
Current EA build: `2.02R0L2 / V2_SP_ARCHITECTURE_RESEARCH_V3`  
Current phase: **D-152 SP V3 MATRIX COMPLETE / V3E PROVISIONAL SP REFERENCE / ENTRY SURVIVAL NEXT**  
V1: **FROZEN HISTORICAL CONTROL**  
2021: **KEEP UNTOUCHED**

## Startup order

For active V2 work:

1. Check latest GitHub commit.
2. Read root `AGENTS.md`.
3. Read `docs/ea/v2/AGENTS_V2.md` as V2 strategy authority.
4. Read root `docs/ea/HANDOFF.md`.
5. Read this file.
6. Read `docs/ea/v2/D152_SP_V3_RESULTS.md`.
7. Read `docs/ea/v2/RESEARCH_STATE_V2.md` and `BACKLOG_V2.md`.
8. Read older D145/D146/D148/D149/D151/D152 design docs only as needed.

If chat memory conflicts with GitHub, GitHub wins.

## Current strategy authority

V2 remains:

```text
EXTERNAL_CONTINUATION only
BASELINE_NO_REGIME_GATE control
ROOT_OB_DISTAL_20
structural objective TP
no reversal order authority
no look-ahead
```

D-152 research results do **not** yet modify `AGENTS_V2.md` or `EA_SPEC_V2.md`.

## D-153 infrastructure status

The automated MT5 batch runner is now validated end-to-end on the D-152 matrix.

Observed successful workflow:

```text
case definition
-> per-run .set/.ini
-> terminal64.exe /config
-> Every tick based on real ticks
-> unique ledger CSV
-> result collection
-> manifest/repro files
-> Desktop ZIP
```

The completed artifact contained all 12 GOLD/BTC D-152 runs and was successfully used for the current analysis.

## D-152 completed result

Read:

`docs/ea/v2/D152_SP_V3_RESULTS.md`

Primary decision:

```text
provisional post-+1R SP reference
= V3E BANK_2R_LOCK_ONE
```

Key evidence:

```text
GOLD V3E:
53 closed
WR 52.83%
final >= +1R 33.96%
avg winner +1.328R
expectancy +0.203R
total +10.783R
DD 6.807R

BTC V3E:
127 fills / 125 closed / 2 right-censored
WR 44.00% on closed
final >= +1R 32.80%
avg winner +1.225R
expectancy -0.022R
total -2.750R
DD 14.233R
```

V3E is **not baseline promotion**. It is the current research reference.

## Why SP research pauses

Fill -> +1R remains the binding ceiling:

```text
GOLD25   30/53 = 56.6%
BTCUSD25 60/127 = 47.2%
```

Post-+1R SP already converts roughly 93-95% of survivors into positive outcomes.

Therefore the project cannot reach the active `>=70%` realized-WR stretch target through exit management alone.

## Current next problem

Primary research returns to:

```text
Fill -> +1R Entry survival
```

Required separation remains:

```text
true HTF/map directional failure
vs
local source failure while HTF survives
vs
same-Root timing / stop sensitivity
vs
correlated repeated Entry failure
```

Do not reuse M30 +1R runner maturity as an Entry filter.

A post-SL recovery/re-entry hypothesis may be studied only with causal shadow measurement first. No real re-entry rule is authorized yet.

## EM status

EM remains experimental.

GOLD showed risk-cluster benefits, but BTC showed a generalization warning because quarantine could discard stronger recovery opportunities.

Do not combine a new Entry rule with EM before the Entry mechanism is understood independently.

## Immediate next work

1. Keep V3E as the provisional post-+1R reference.
2. Stop same-sample D-152 threshold tuning.
3. Use the D151/D148 failure taxonomy to formulate the next Entry-survival causal audit.
4. Implement shadow-only instrumentation before real Entry/re-entry changes.
5. Use D-153 batch automation for GOLD25/BTC25 validation.
6. Preserve right-censoring and execution-integrity requirements.
