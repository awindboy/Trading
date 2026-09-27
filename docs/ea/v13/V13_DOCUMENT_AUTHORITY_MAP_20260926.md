# V13 document authority map

As of `2026-09-28`, this update was prepared against GitHub `main` HEAD
`53457bf5a38b0da0b77da094b6ea0223bc238fab`. Always refresh `main` before
using this map; a later GitHub commit takes precedence.

Read V13 authority in this order:

1. `AGENTS_V13.md` — active generation, frozen baseline, causal discipline and
   completed first HA-8A diagnostic boundary.
2. `HANDOFF_V13.md` — shortest current resume point.
3. `RESEARCH_STATE_V13.md` — consolidated evidence through the first HA-8A and active
   question.
4. `V13_HA_KNOWLEDGE_AND_SOURCE_REGISTER_20260926.md` — original source map.
5. `V13_HA_KNOWLEDGE_AND_SOURCE_REGISTER_ADDENDUM_20260927.md` — platform
   references and local evidence added during HA-6/HA-7.
6. `V13_HA_RESEARCH_ROADMAP_20260926.md` — original ordered research program.
7. `V13_HA_RESEARCH_ROADMAP_STATUS_ADDENDUM_20260928.md` — current status and
   next hypothesis. Its 2026-09-27 predecessor is historical.
8. `V13_BASELINE0_HA_MAX10_CONTRACT_20260926.md` — exact Baseline-0 semantics.
9. `V13_EXECUTION_RECOVERY_20260926.md` — runtime failure/recovery semantics.
10. `V13_MQL5_BACKTEST_PROTOCOL_20260926.md` — official tester requirements.
11. HA-3/4/4C/4D/5 contracts — earlier consumed observation definitions.
12. `V13_HA6A_HASTOC_OBSERVATION_CONTRACT_20260927.md`.
13. `V13_HA6B1_EMA50_CONTEXT_OBSERVATION_CONTRACT_20260927.md` and
    `V13_HA6B2_EMA20_ENVELOPE_OBSERVATION_CONTRACT_20260927.md`.
14. `V13_HA6C_ATR_NORMALIZATION_OBSERVATION_CONTRACT_20260927.md`.
15. `V13_HA6D1_ADX_WILDER_OBSERVATION_CONTRACT_20260927.md`.
16. `V13_HA6E_TICK_VOLUME_PARTICIPATION_CONTRACT_20260927.md` and
    `V13_HA6E2_H1_OPPOSITION_PARTICIPATION_CONTRACT_20260927.md`.
17. `V13_HA7_FIRST_ACTION_CHILD_ADMISSION_CONTRACT_20260927.md` — first
    action experiment; its receipt rejects the action.
18. `V13_HA6_HA7_RESEARCH_SYNTHESIS_20260927.md` — cross-stage mechanism
    synthesis; use together with individual receipts, not instead of them.
19. `V13_HA8A_COMBINATION_MODEL_CONTRACT_20260928.md` — fixed first model ladder,
    temporal split, payoff/tail diagnostic and no-action boundary.
20. `results/README.md` and the HA-0..HA-8A receipts. For exact numbers and
    caveats, the stage receipt controls over prose summaries.
21. `../../../mt5/experts/V13HAOnlyMax10EA.mq5` — frozen Baseline-0 EA.
22. `../../../mt5/tester/V13HAOnlyMax10.GOLD.actualticks.2024_2026.ini` —
    tester starter configuration.

## Precedence

- V13 controls active strategy research. V12 and earlier are history/evidence.
- Baseline-0 contract controls trading semantics until a later accepted action
  contract explicitly replaces part of it.
- Individual stage contracts define what was allowed to be measured/tested.
- Individual result receipts control exact measured numbers and limitations.
- The HA-6/HA-7 synthesis explains cross-stage interpretation but cannot invent
  authority absent from a receipt.
- The HA-7 action was **rejected** and has no EA authority.
- The first HA-8A model diagnostic is complete as observation only. It did not
  solve economic Child-loss selection. No prediction threshold or trade action
  is authorized until a later frozen action contract and required validation.
- MetaQuotes platform/reference semantics outrank community formulas where they
  conflict. External strategy examples are research leads, never edge proof.
