# V13 document authority map

As of `2026-09-27`, read V13 authority in this order:

1. `AGENTS_V13.md` — generation boundary, frozen baseline, causal rules and
   research discipline.
2. `HANDOFF_V13.md` — shortest resume point and immediate next work.
3. `RESEARCH_STATE_V13.md` — current evidence, tester status and active question.
4. `V13_HA_KNOWLEDGE_AND_SOURCE_REGISTER_20260926.md` — source-backed HA
   knowledge map, source authority classes and combination leads.
5. `V13_HA_RESEARCH_ROADMAP_20260926.md` — ordered one-component-at-a-time HA
   research program.
6. `V13_BASELINE0_HA_MAX10_CONTRACT_20260926.md` — exact strategy semantics.
7. `V13_EXECUTION_RECOVERY_20260926.md` — current runtime failure/recovery
   semantics.
8. `V13_MQL5_BACKTEST_PROTOCOL_20260926.md` — exact tester setup and required
   report fields.
9. `V13_HA3_REPRESENTATION_COMPARISON_CONTRACT_20260927.md` — named,
   observation-only four-representation comparison; not a strategy rule.
10. `V13_HA4_MTF_OBSERVATION_CONTRACT_20260927.md` — D1 then H1 causal,
    observation-only comparison; no MTF action authority.
11. `V13_HA4C_INTEGRATED_STATE_CONTRACT_20260927.md` and
    `V13_HA4D_EMA_MORPHOLOGY_CONTRACT_20260927.md` — observation-only
    supplements correcting the color-heavy HA-3/4 scope.
12. `V13_HA5_CAUSAL_RAW_SWING_CONTRACT_20260927.md` — frozen first
    observation-only raw-price swing probe; no trading rule.
13. `results/README.md` — compact result routing, including HA-5.
14. `results/V13_HA5_CAUSAL_RAW_SWING_RECEIPT_20260927.md` — causal raw
    swing interactions, H1-warning comparison and tail counterexamples.
15. `results/V13_HA4C_D_INTEGRATED_STATE_RECEIPT_20260927.md` — same-Journey
    morphology, ordered-H1, FAST/D1 and EMA-wick evidence; no action rule.
16. `results/V13_BASELINE0_EXTENDED_ACTUAL_TICK_DIAGNOSTIC_20260926.md` — latest
    actual-tick structural-parity diagnostic; not the official exact-window
    economic receipt.
17. `../../../mt5/experts/V13HAOnlyMax10EA.mq5` — frozen Baseline-0 MQL5
    implementation.
18. `../../../mt5/tester/V13HAOnlyMax10.GOLD.actualticks.2024_2026.ini` — starter
    tester configuration; Strategy Tester GUI remains broker/account authority.

## Precedence

V13 controls active strategy research. V12 and earlier remain historical.

The knowledge/source register and research roadmap define research order only;
they do not modify Baseline 0. A new trading rule requires a separate named V13
contract and a full-window comparison.

Execution revision 13.002 supersedes the initial halt-on-any-order-failure
paragraph. Use the same execution revision for all economic comparators unless a
later explicit execution-only revision replaces it.

MetaQuotes standard HA semantics are the formula authority. Community variants
that use different formulas or smoothing are separate representations and must
be named as such; they cannot silently redefine standard HA.
