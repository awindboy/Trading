# V12 Phase 1U — multi-speed HA ownership-transition contract

Status: **frozen before Phase-1U outcome evaluation / consumed-development only**

## Question

Did V10 lose useful FAST/STD/SLOW interaction by granting FAST alone the run,
Child, and reversal clock while retaining STD/SLOW only as static ML features?
Phase 1U tests whether a threshold-free, chronological three-speed ownership
grammar separates avoidable V10 stopped Children from profitable Children.

This is a component reverse-engineering diagnostic. It does not let HA create a
V12 CRT candidate and cannot alter the active V12 assembly.

## Fixed sources and population

- verified GOLD# raw M1 through `2026-08-28 23:57`;
- the complete causal V10 opportunity universe rebuilt from that M1 prefix;
- the supplied MT5 V10 R7G event ledger;
- fixed economic window `2024-10-01 00:00` through `2026-08-28 12:00`;
- exact selected population: MT5 `r7g_weight > 0`;
- primary unit: one selected Child, not one risk-unit or one R-dollar.

The full 6,770-row V10 universe is used only for state coverage and stability.
Economic comparisons use the exact selected MT5 population and its frozen
weights. GOLD# 2021 remains sealed.

## Causal ownership grammar

At every completed H4 decision, classify the current FAST direction before
updating memory. `memory_owner_before` is the most recent direction established
on a strictly earlier completed H4 for which STD and SLOW agreed. STD/SLOW
disagreement preserves that memory.

For the current FAST direction:

1. `FAST_WITH_MEMORY`: FAST equals prior memory;
2. `FAST_ONLY_CHALLENGE`: FAST opposes memory and neither STD nor SLOW agrees
   with FAST;
3. `STD_LEADS_TRANSFER`: FAST opposes memory, STD agrees with FAST, and SLOW
   remains opposed;
4. `SLOW_ONLY_CONFLICT`: FAST opposes memory, SLOW agrees with FAST, and STD
   remains opposed;
5. `TRANSFER_CONFIRMED`: FAST opposes memory and both STD and SLOW agree with
   FAST;
6. `MEMORY_UNAVAILABLE`: no prior STD/SLOW agreement exists.

After classification, current STD/SLOW agreement updates memory. No run length,
future return, stop, settlement, or outcome may influence the state.

At FAST `k1`, `FAST_WITH_MEMORY` means a return/resumption to the prior owner;
the four opposing states describe stages of a challenge or transfer. For
`k2+`, the same grammar records whether the FAST run has earned ownership or is
still moving against remembered ownership.

## Frozen counterfactuals

The primary `OWNERSHIP_AUTHORIZED` view keeps an existing selected V10 Child
only when its state is `FAST_WITH_MEMORY` or `TRANSFER_CONFIRMED`. It preserves
the original entry, Hard SL, exit, R, and MT5 R7G weight.

The explanatory `K1_OWNERSHIP_ONLY` view applies the same condition only to
`k1` and preserves every selected `k2+` Child. It exists only to determine
whether any effect comes from new-run authorization or from broad exposure
removal. Neither view creates a replacement strategy.

## Count-first evaluation

Report for control, retained, removed, and state cells:

- selected Children;
- Hard-SL Children and Hard-SL rate;
- all negative-R and positive-R Children;
- positive Children in `<1R`, `1–3R`, `3–5R`, and `>=5R` buckets;
- first, repeat, and alternating-direction stop chains;
- maximum stop streak;
- year, side, and `k1/k2/k3+` stability;
- funded units and R only as secondary diagnostics.

The primary count gate requires all of:

- at least `20%` fewer Hard-SL Children;
- at least `90%` positive-Child retention;
- at least `90%` retention of both `>=3R` and `>=5R` Child counts;
- at least `2.0` avoided Hard-SL Children per lost positive Child;
- no lower Child win rate and no worse maximum stop streak;
- no side with a higher Hard-SL rate;
- at most one calendar year with a higher Hard-SL rate.

These gates prevent a large reduction in trading frequency or a few retained
outliers from masquerading as stop recognition. Passing consumed-history gates
would still grant no entry, veto, sizing, trade, EA, or production authority.

## Explicit non-questions

Phase 1U does not retest whole-base STD replacement, all-three-color alignment,
a fixed confirmation delay, the V11 STD+SLOW-only skeleton, or a tuned bridge
age. It tests only whether FAST events have different meanings relative to
causal STD/SLOW ownership memory.
