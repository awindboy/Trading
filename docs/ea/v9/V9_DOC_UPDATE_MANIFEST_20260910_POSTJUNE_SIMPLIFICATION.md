# V9 Document Update Manifest — Post-June Simplification

Date: `2026-09-10`
Base GitHub HEAD used for preparation: `f7ad1bb8f1be47303a41c66231bf0f21c4f928dd`

## Active files added/replaced by this bundle

```text
docs/ea/v9/AGENTS_V9.md
docs/ea/v9/HANDOFF_V9.md
docs/ea/v9/RESEARCH_STATE_V9.md
docs/ea/v9/DECISIONS_V9_POSTJUNE_SIMPLIFICATION_AND_RUNTIME_ADDENDUM_20260910.md
docs/ea/v9/V9_CAUSAL_NUMERIC_ANALYSIS_AND_TOOLING_PROTOCOL_20260910.md
docs/ea/v9/V9_DETERMINISTIC_EXECUTION_RUNTIME_AND_STRUCTURE_PACKET_PROTOCOL_20260910.md
docs/ea/v9/V9_DISCRETIONARY_TRADING_PIPELINE_POSTJUNE_20260910.md
docs/ea/v9/V9_NEXT_RESEARCH_CONTRACT_POSTJUN_EXECUTION_RUNTIME_20260910.md
docs/ea/v9/V9_POSTJUNE_RETAINED_VS_SIMPLIFIED_AUDIT_20260910.md
docs/ea/v9/results/V9_JUN25_EXECUTION_ENVIRONMENT_POSTMORTEM_20260910.md
```

## Authority change

The June-specific pipeline and June next-research contract become consumed historical authority.

The post-June active stack is:

```text
stable V9 mindset
+ post-June simplification decision addendum
+ causal numeric tooling 20260910
+ deterministic execution runtime 20260910
+ post-June minimal AI pipeline 20260910
+ post-June execution-runtime research contract
```

## Main changes

- preserve baseball / convex payoff philosophy;
- preserve Parent/Child separation;
- preserve Hard SL and no-rescue rule;
- preserve opposite-side audit;
- reduce mandatory AI taxonomy/prose;
- move objective structure/geometry to code;
- remove automatic nearest-level `CP1` semantics;
- require forward structure geometry;
- use event-driven Parent-Journey reviews with H1 heartbeat;
- block new future-hidden replay until runtime parity passes;
- keep `GOLD# 2021` untouched.
