# D-154F Causal Lineage Results

Status: `COMPLETE / NO STRATEGY PROMOTION`  
Date: `2026-08-22`

## Question

D-154F tested whether the existing M1 `SEQUENCE_ONLY` chain was failing because the accepted CHoCH did not directly break the opposite-correction protected boundary frozen at the accepted sweep, and then explored the sweep-time M1 state without changing strategy authority.

## Non-interference

GOLD23 Q1 audit OFF/ON canonical parity passed after removing D154F-only rows and normalizing the diagnostic `csv_rows_written` counter. Entry, SL, TP, orders and baseline execution rows were unchanged.

## Discovery and validation

The pre-registered `DIRECT_FROZEN_BREAK` hypothesis was not supported in GOLD23 discovery.

A secondary GOLD23 discovery signal appeared at accepted-sweep bar start:

```text
M1 mature structure: 33 / 58 = 56.9% Fill -> +1R
M1 TRANSITION:         1 / 7  = 14.3%
```

One additional TRANSITION observation was right-censored and was not imputed.

The relationship did not generalize. Pre-registered validation:

```text
GOLD24    TRANSITION 28.6% vs non-TRANSITION 48.9%
GOLD25    TRANSITION 40.0% vs non-TRANSITION 58.3%
SILVER25  TRANSITION 33.3% vs non-TRANSITION 40.5%
BTC25     TRANSITION 54.5% vs non-TRANSITION 46.6%  (reversed)
CADJPY25  TRANSITION 33.3% vs non-TRANSITION 26.0%  (reversed)

validation pooled:
TRANSITION      16 / 41  = 39.0%
non-TRANSITION 146 / 350 = 41.7%
```

Therefore `TRANSITION at sweep` is rejected as an Entry veto.

The direct-frozen-boundary relation also lacked discovery support and showed inconsistent market/year direction; it is not promoted.

## Research consequence

D-154A/B/C/F collectively weaken the idea that a small M1 confirmation refinement is the main Fill -> +1R bottleneck. D-154D also rejected a universal new-Root-after-failure rescue out of sample.

Research priority moves upstream to the causal validity of the HTF map / Root relationship at Root birth. Baseline strategy semantics remain unchanged.
