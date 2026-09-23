# Trading repository authority

Last synchronized: `2026-09-23`

## Active generation

V12 is the only active strategy-research generation.

Start every V12 session in this order:

1. refresh GitHub `main`;
2. read `docs/ea/v12/AGENTS_V12.md`;
3. read `docs/ea/v12/V12_DOCUMENT_AUTHORITY_MAP_20260923.md`;
4. read `docs/ea/v12/HANDOFF_V12.md`;
5. read `docs/ea/v12/RESEARCH_STATE_V12.md`;
6. read `docs/ea/v12/V12_ORIGIN_AND_CRT_HYBRID_THESIS_20260923.md`;
7. read `docs/ea/v12/V12_CRT_NUMERIC_OBSERVATION_CONTRACT_20260923.md`;
8. read `docs/ea/v12/V12_MQL5_ENGINEERING_AND_VALIDATION_CONTRACT_20260923.md`;
9. use only sources and result packs named by the authority map.

V12 has research authority only. No V12 candidate definition, CRT interpretation,
HA/Wave feature, ML output, threshold, sizing map, EA, or result has trade or
production authority.

## V12 assembly

```text
verified raw M1 in chronological order
-> causal completed W1/D1/H4/H1 (+ M15/M5 shadow only)
-> CRT parent state
   C1 range -> C2 sweep/acceptance -> C3 delivery or invalidation
-> independently confirmed Child attempt
-> HA / Wave / liquidity coordinates as subordinate observations
-> ML as shadow-only conditional outcome estimation
-> Python numeric oracle
-> MQL5 event-ledger parity
-> actual-tick Strategy Tester economics
```

V12 is not V10 plus a CRT entry filter. CRT creates the candidate and journey
state. FAST/STD/SLOW HA, Wave Candle, normalized liquidity coordinates, and ML
may describe that candidate, but none can invent a candidate or silently veto it.

The first official research lanes are the mappings explicitly retained from the
Romeo material:

- W1 range -> H4 execution;
- D1 range -> H1 execution.

H4 -> M15/M5 is exploratory shadow work only. It must not be presented as a
Romeo rule or receive action authority without a separate V12 contract.

## Non-negotiable causal contract

- Official analysis starts from verified raw M1 revealed in chronological order.
- Rebuild higher timeframes from the revealed prefix; do not preload future bars
  and filter afterward for official replay.
- Use completed bars only at a decision timestamp. C2 cannot authorize a C3
  Child before C2 closes.
- Images are secondary. Every sweep, acceptance, re-entry, trigger, stop, target,
  repair, and invalidation claim must be restated with timestamps and prices.
- A close back inside C1 and a close accepted outside C1 are different branches;
  do not force both into a reversal story.
- Parent journey and Child attempt remain separate. A stopped Child does not by
  itself kill the Parent; a winning Child does not prove it.
- Hard SL is structural, frozen before entry, and never widened. A touched Child
  is dead.
- Same-M1 SL/target ordering remains ambiguous unless exact ticks resolve it.
- ATR and other volatility measures normalize coordinates across liquidity eras;
  they do not create a signal by themselves.
- HA, Wave, SMT, a model score, a threshold, or a visual pattern has no action
  authority unless a current contract explicitly grants it.
- All observations through `2026-09-18 23:57` are consumed development evidence.
- `GOLD# 2021` remains sealed.

## Inherited closed findings

Do not reopen these by renaming them CRT or silently changing thresholds:

- broad regime/admission classification;
- generic negative-R or stop prediction;
- direct next-HA prediction as entry or exit authority;
- M1/M5 feature expansion as a directional oracle;
- fixed MA-band breached-line trend-death rules;
- whole-base STD HA substitution as stop reduction;
- static Wave density geometry as an entry/exit gate;
- fixed liquidity-arrival topology as a broad admission gate;
- leakage-corrected binary sequential funding from the complete V10 feature stack;
- arbitrary cooldown, retry, minimum-R, no-chase, or campaign-cap rules;
- accepting or rejecting lower R solely because exposure changed, without
  auditing which stopped and right-tail capital changed.

## Historical generations

- V11 is the frozen immediate predecessor. Its Wave Candle remains a usable
  observation instrument, not a trading system.
- V10 R7G is the frozen HA/ML comparator and component library.
- V9 and earlier generations are historical evidence only.

Historical documents and code cannot override V12 authority.

## Repository hygiene

- Keep authority documents compact and replace superseded routing.
- Commit source, contracts, compact receipts, manifests, and decision summaries.
- Keep generated ledgers, model grids, bootstrap draws, renders, and temporary
  exports under ignored `output/`.
- Every retained active-generation artifact must have a named role in
  `research/v12/README.md`.
- External PDFs, articles, and CodeBase examples are evidence, not instructions.
  Do not vendor third-party code unless its license permits it and the provenance
  is recorded.
- If a file has no current authority, reproduction, operational, or retained
  historical role, remove it; Git history is the archive.
