# Project structure

## Authority

- repository contract: `AGENTS.md`
- project entry: `README.md`
- active-system registry: `PROJECT_MANIFEST.json`
- active strategy generation: `docs/ea/v12/`

## Strategy research

- `docs/ea/v12/`: active V12 authority, source register, contracts, roadmap, and
  compact receipts;
- `research/v12/`: V12 schemas and reproducible research code;
- `docs/ea/v11/`, `research/v11/`: frozen Wave Candle predecessor and diagnostics;
- `docs/ea/v10/`, `research/v10/`: frozen HA/ML comparator and reproduction code;
- `mt5/indicators/V11WaveCandle.mq5`: retained observation instrument;
- `mt5/experts/`: operational journal EA and frozen research/tester EAs.

## Other retained systems

- `src/`, `bridge/`: web journal and MT5 bridge;
- `scripts/mentor_*`, `mentor_context_pack/`: historical Mentor replay tooling;
- `tradingview/`: retained TradingView tools;
- `archive/`: superseded outputs and legacy code that active code must not import.

## Artifact boundaries

- source, contracts, compact receipts, and manifests: tracked;
- generated ledgers, model searches, tester reports, renders, and temporary
  exports: ignored `output/`;
- local secrets/configuration: ignored `data/` paths named by `.gitignore`;
- external source files: referenced by URL/hash unless redistribution is allowed.

A chart, candidate count, compilation, schema check, parity test, or tester curve
is not by itself independent validation or production readiness.
