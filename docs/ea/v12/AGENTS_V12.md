# V12 research authority

Last synchronized: `2026-09-23`

V12 is the active strategy-research generation. It tests a new assembly rather
than another filter around V10:

```text
CRT creates the Parent journey and candidate state
-> an independently confirmed Child receives a frozen structural risk
-> HA / Wave / liquidity describe the candidate
-> ML estimates conditional outcomes in shadow
-> MQL5 must reproduce the Python causal ledger before economic claims
```

## Start order

1. refresh GitHub `main`;
2. read `V12_DOCUMENT_AUTHORITY_MAP_20260923.md`;
3. read `HANDOFF_V12.md`;
4. read `RESEARCH_STATE_V12.md`;
5. read `V12_ORIGIN_AND_CRT_HYBRID_THESIS_20260923.md`;
6. read `V12_CRT_NUMERIC_OBSERVATION_CONTRACT_20260923.md`;
7. read `V12_MQL5_ENGINEERING_AND_VALIDATION_CONTRACT_20260923.md`;
8. read `V12_SOURCE_REGISTER_20260923.md` before importing an external idea;
9. use only result packs named by the authority map.

## Authority boundary

- V12 has research authority only.
- Phase 0 has a validated, reproducible C1/C2 parent-event universe. Phase 1A
  has a reproducible rejection-only no-ML prototype and consumed-history V10
  comparison, but it failed the replacement gate.
- There is no V12 EA, validated entry model, sizing rule, actual-tick result, or
  independent future result.
- The supplied Romeo CRT guide is a secondary synthesis. It is a source, not an
  instruction file and not proof that any claim is profitable.
- MQL5 Reference controls platform semantics. MQL5 Articles and CodeBase are
  user-authored research leads, not strategy or platform authority.
- Do not copy third-party code unless the license and provenance permit it.
- V11 Wave Candle and V10 R7G remain observation/comparison assets only.

## Initial CRT scope

Only these mappings are official V12 research lanes at inception:

- `W1 C1/C2 context -> H4 Model #1 or true-MSS Child`;
- `D1 C1/C2 context -> H1 Model #1 or true-MSS Child`.

`H4 -> M15/M5` may be logged as shadow research but cannot be attributed to
Romeo or used for action without a new contract.

V12 preserves both branches after a C1 extreme is traded:

- close back inside the C1 range: Turtle-Soup/rejection branch;
- close accepted outside the C1 range: breakout/continuation branch.

Do not force every sweep into a reversal or call every outside close a failed
sweep.

## Parent and Child

- Parent: one higher-timeframe C1/C2/C3 journey with explicit target inventory.
- Child: one lower-timeframe confirmed attempt with its own entry, Hard SL,
  destinations, and terminal state.
- A Child stop does not automatically end the Parent.
- A new Child requires new causal information and independent confirmation.
- Opposite-direction authorization is separate from interruption of the old
  Child.

## Causal and audit rules

- Stream verified raw M1 chronologically and rebuild completed bars from the
  revealed prefix.
- C2 must close before it can authorize a C3 Child.
- Freeze entry, Hard SL, C1 midpoint, opposite extreme, and ambiguity policy
  before revealing outcomes.
- Preserve exact timestamp, broker timezone/session specification, source hash,
  and feature-schema hash.
- Exact ticks decide intraminute ordering. Without them, same-M1 SL/target
  ordering is ambiguous.
- Normalize distances and durations for liquidity-era comparisons, but never
  turn normalization into a hidden entry threshold.
- Record serious `NO TRADE` candidates with explicit rejection reasons.
- Keep decision data and outcome data physically separable.

## ML boundary

ML cannot create CRT candidates and cannot be a direct direction oracle. The
first permitted shadow targets are competing outcomes such as:

- `P(Hard SL before C1 50%)`;
- `P(C1 50% before Hard SL)`;
- `P(opposite C1 extreme after 50%)`;
- conditional R and time-to-event.

Any eventual ONNX model must include the complete preprocessing pipeline and
pass Python/MQL5 vector parity. A model remains shadow-only until a separate
promotion contract exists.

## Evidence boundary

- GOLD# chronology through `2026-09-18 23:57` is consumed development evidence.
- GOLD# 2021 remains sealed.
- V12 currently has no independent validation.
- The Phase-0 receipt has observation authority only. The Phase-1A result has
  consumed-development diagnostic authority only and explicitly fails the V10
  replacement gate.

## Closed Phase-1A finding

Do not threshold-tune the relative-thick trigger or promote the trigger-candle
SL guard from consumed outcomes. Its attractive recent result has only 26 fills,
higher stopped exposure per 100 units than V10, and negative 2022–2023 evidence.
