# V5 Decisions — D-183 to D-184

Date: `2026-08-27`
Production authority: `NONE`

## D-183 — D-145 M30 state is portable as a measurement, not as inherited strategy state

Decision:
- the exact D-146 M30 protected/external progress definition may be reconstructed outside V3;
- the measurement is derived from global closed-bar `V1StructureState` and does not require Root/FVG/scenario identity;
- only an exact causal replay of the frozen V1 structure semantics is acceptable;
- generic swing/pivot approximations have no authority.

Reason:
V1 code inspection shows structure state is created and updated before Root/FVG/scenario side effects. Stage-0 delayed-start QA also found exact agreement wherever both replays had a valid state.

This decision authorizes measurement only, not a First Cross rule.

## D-184 — V5-036A transfer fails; close First Cross payoff-rescue

Frozen inherited prediction:

```text
median progress(+2R runner) < median progress(exhaust)
```

Observed First Cross transfer:

```text
pooled runner median   1.007361
pooled exhaust median  0.964935
```

Breadth:
- only 2/4 comparable markets support the inherited sign;
- only 2023 supports it; 2024 and 2025 reverse;
- both LONG and SHORT reverse;
- 3/9 comparable cells support the inherited sign.

Decision:

```text
CROSS-ARCHITECTURE TRANSFER FAIL
FIRST CROSS PAYOFF-RESCUE CLOSED
```

Forbidden rescue:
- no `one_r_m30_range_progress` threshold;
- no market removal;
- no direction veto;
- no First Cross partial/BE/EMA/slow retuning;
- no revival of V5-034A promotion validation;
- no GOLD# 2021 inspection.

Next research must be a genuinely new success-first/payoff-first mechanism under D-180, not a First Cross patch.
