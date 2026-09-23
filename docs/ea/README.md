# EA strategy research documentation

Last synchronized: `2026-09-23`

## Active research

V12 is the only active strategy-research generation.

```text
repository AGENTS.md
-> docs/ea/v12/AGENTS_V12.md
-> V12_DOCUMENT_AUTHORITY_MAP_20260923.md
-> HANDOFF_V12.md
-> RESEARCH_STATE_V12.md
-> V12_CRT_NUMERIC_OBSERVATION_CONTRACT_20260923.md
-> V12_MQL5_ENGINEERING_AND_VALIDATION_CONTRACT_20260923.md
```

V12 uses CRT as the candidate and Parent-journey grammar, then studies HA,
Wave Candle, normalized liquidity coordinates, and ML as subordinate evidence.
It has no trade or production authority.

## Historical generations

- V11: frozen immediate predecessor; Wave Candle remains an observation asset;
- V10: frozen HA/ML predecessor and principal comparator;
- V9 and earlier: historical evidence only.

Historical documents cannot override V12 authority.

## Artifact policy

- authority and checkpoints: `docs/ea/v12/`;
- schema and retained code: `research/v12/`;
- large generated ledgers and model output: ignored `output/`;
- external sources: register links and provenance, do not silently vendor code;
- deleted superseded packs: Git history.

The retained V10 replay EAs remain research/tester artifacts. The user's MT5
run exposed market-closed order failures; that execution-lifecycle repair is
deferred and must not be relabeled as a strategy loss or filled retrospectively.
