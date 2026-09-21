# Trading repository authority

Last synchronized: `2026-09-21`

## Active generation

V10 is the only active strategy-research generation.

Start every V10 session in this order:

1. refresh GitHub `main`;
2. read `docs/ea/v10/AGENTS_V10.md`;
3. read `docs/ea/v10/V10_DOCUMENT_AUTHORITY_MAP_20260921.md`;
4. read `docs/ea/v10/HANDOFF_V10.md`;
5. read `docs/ea/v10/RESEARCH_STATE_V10.md`;
6. read `docs/ea/v10/V10_NEXT_RESEARCH_CONTRACT_NORMALIZED_STATE_FORWARD_20260921.md`;
7. use the result packs named by the authority map only.

V10 has research authority only. No V10 rule, model, sizing map, threshold, EA, or result has production authority.

## Current V10 direction

```text
H4 FAST HA
-> primary campaign and participation clock

R4 / R5 / R7G
-> frozen historical comparator and executable research artifact

normalized H4/H1/M15 state
-> shadow observation only
-> same-timeframe causal ATR180 for price distances and slopes
-> scale-free line fractions for MA-ribbon support and penetration

future chronology after 2026-08-28
-> only valid new evidence
```

The current research objective is not generic regime classification or next-H4 color prediction. It is to reduce avoidable stopped Children without deleting the persistent-run right tail that pays for V10.

## Non-negotiable causal tooling contract

- Official analysis starts from verified raw M1 in chronological order.
- Rebuild higher timeframes from the revealed M1 prefix; do not preload future bars and filter afterward for official replay.
- Images are secondary visualization. Entry, rejection, Hard SL, exit, repair, and departure claims must be restated in numeric price terms.
- Use only completed information available at the decision timestamp.
- Once a Child touches Hard SL, it is dead. No future movement may rescue it.
- Same-M1 ordering ambiguity must remain ambiguous unless exact ticks resolve it.
- A model, score, threshold, MA line, or visual pattern has no action authority unless a current contract grants it.
- All 2022-2026 observations through `2026-08-28 23:57` are consumed development evidence.
- `GOLD# 2021` remains sealed.

## Current closed findings

Do not reopen these by silently changing thresholds:

- broad regime/admission classification;
- generic negative-R prediction;
- direct next-HA prediction as entry or exit authority;
- M1/M5 feature expansion as a directional oracle;
- progression proof and damage-repair lockouts;
- fixed MA-band breached-line trend-death rules;
- post-hoc `no-k3p-SHORT` exclusion;
- arbitrary cooldown, retry, minimum-R, no-chase, or campaign-cap rules.

## Historical generations

V9 is the frozen predecessor and comparator. V8 and earlier generations are historical evidence only. Their documents and Git history do not override V10. Read an older generation only when the current V10 authority explicitly routes to it or when reproducing a named historical result.

## Repository hygiene

- Keep authority documents compact and replace superseded routing instead of appending another override block.
- Commit compact receipts, manifests, and decision summaries only.
- Keep large generated ledgers, bootstrap draws, model-search grids, temporary exports, and local replay outputs under ignored `output/`.
- Every retained research script must have a named role in `research/v10/README.md`.
- If a file's purpose cannot be stated from current authority, current reproduction, or a retained historical decision, remove it; Git history is the archive.
