# V2 EA Specification — Continuation-Only Fork

Status: `ACTIVE DEVELOPMENT SPEC`
Authority: `docs/ea/v2/AGENTS_V2.md`
Implementation target: `2.00R0L0 / V2_CONTINUATION_ONLY_BOOTSTRAP`
2021: `KEEP UNTOUCHED`

## 1. Purpose

V2 is a clean continuation-only development line. It exists so trend-following research no longer mixes with historically weak reversal execution or with V1's frozen compatibility obligations.

V2 is forked from V1/D149 V2 code for deterministic execution compatibility, but V1 itself is not edited.

## 2. Scope contract

Allowed:

```text
V1_SCOPE_EXTERNAL_CONTINUATION
```

Forbidden as V2 trading authority:

```text
V1_SCOPE_EXTERNAL_REVERSAL
V1_SCOPE_NONE
INTERNAL_ROTATION first-position execution
```

The legacy reversal enum and map bookkeeping may remain compile-compatible inside the fork. The scenario builder must fail closed before assigning `EXTERNAL_REVERSAL` to a V2 draft.

## 3. V2 identity / isolation

The V2 EA must use a distinct:

```text
EA filename
build identity
phase identity
magic-number default
event-CSV default
```

so V1 and V2 tester results cannot be confused.

Target defaults:

```text
EA = mt5/experts/MentorDeterministicV2EA.mq5
build = 2.00R0L0
phase = V2_CONTINUATION_ONLY_BOOTSTRAP
magic = 26082202
regime = BASELINE_NO_REGIME_GATE
sizing = FIXED_RISK_MONEY
exit = ORIGINAL
EM = OFF
```

## 4. Strategy control

V2 control changes only one strategic fact relative to the inherited execution core:

```text
reversal first-position authorization = disabled
```

Entry chain, initial SL, objective freeze, pending lifecycle, and structural TP remain inherited controls.

SP V2 / EM V2 remain research toggles. Their presence in the source does not make them baseline authority.

## 5. Required bootstrap validation

Before using V2 profitability evidence:

1. MetaEditor compile: `0 errors`.
2. Run a short `ORIGINAL + EM_OFF` V2 smoke.
3. Analyzer must confirm `reversal_plans = 0`, `reversal_fills = 0`, `reversal_closes = 0`.
4. Execution divergence / cancel rejection / unresolved fills must be zero for evidence classified clean.
5. Re-run GOLD/BTC continuation research under V2 rather than comparing all-scope equity curves.

## 6. Research metrics

Always report at least:

```text
fills / closed / unresolved
realized WR
avg winner R
avg loser R
expectancy R/trade
total R
max DD R
longest nonpositive streak
+1R survival
+2R conditional survival
post-+2R giveback / retained R
winner concentration
```

SP and EM must also report their own action/state counts.
