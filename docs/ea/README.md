# EA strategy research documentation

Last synchronized: `2026-09-21`

## Active research

V10 is the only active strategy-research generation.

```text
repository AGENTS.md
-> docs/ea/v10/AGENTS_V10.md
-> V10_DOCUMENT_AUTHORITY_MAP_20260921.md
-> HANDOFF_V10.md
-> RESEARCH_STATE_V10.md
-> V10_NEXT_RESEARCH_CONTRACT_NORMALIZED_STATE_FORWARD_20260921.md
```

V10 is HA-primary research with normalized-state forward shadow observation. It has no production authority.

## Historical generations

- V9: frozen predecessor and principal comparator;
- V8 and earlier: historical research and implementation evidence;
- deterministic V1/V2, Ground Truth, Gemini replay, and older regime work: use only when reproducing a named historical result.

Historical documents cannot override V10 current authority.

## Current V10 artifact policy

- authority and checkpoints: `docs/ea/v10/`;
- compact manifests/receipts: `docs/ea/v10/results/`;
- retained code inventory: `research/v10/README.md`;
- large generated ledgers and model-search outputs: ignored `output/`;
- deleted predecessor packs: Git history.

## Current EA boundary

The retained V10 EAs are:

- `mt5/experts/V10R7G_ExactActualTickReplayEA.mq5`;
- `mt5/experts/V10R7G_FullEmbeddedML_EA.mq5`.

They are research/tester artifacts. The user's MT5 run exposed market-closed order failures; the lifecycle fix is deferred to a later EA upgrade and does not change current strategy research authority.

## Working rule

Chat is the working surface. GitHub is the Single Source of Truth. Replace superseded routing instead of appending another override block.
