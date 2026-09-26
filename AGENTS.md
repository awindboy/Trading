# Trading repository authority

Last synchronized: `2026-09-26`
Base GitHub HEAD before V13 update: `b57be8e619254191f3a54da86bec3745edae6ac8`

## Active generation

V13 is the only active strategy-research generation.

V13 is a deliberate reset. It does not continue the V12 feature stack. It starts
again from a minimal Heikin-Ashi trading skeleton and adds complexity only when a
single added component earns its place on the frozen full comparison window.

Start every V13 session in this order:

1. refresh GitHub `main`;
2. read `docs/ea/v13/AGENTS_V13.md`;
3. read `docs/ea/v13/V13_DOCUMENT_AUTHORITY_MAP_20260926.md`;
4. read `docs/ea/v13/HANDOFF_V13.md`;
5. read `docs/ea/v13/RESEARCH_STATE_V13.md`;
6. read `docs/ea/v13/V13_BASELINE0_HA_MAX10_CONTRACT_20260926.md`;
7. read `docs/ea/v13/V13_MQL5_BACKTEST_PROTOCOL_20260926.md`;
8. read the current compact result receipt under `docs/ea/v13/results/`;
9. inspect `mt5/experts/V13HAOnlyMax10EA.mq5` before changing execution semantics.

Where V13 conflicts with V12 or older strategy-routing documents, V13 controls.
Older generations remain historical evidence and must not silently re-enter the
active strategy.

## Frozen V13 Baseline 0

```text
market: GOLD#
clock: completed H4 bars
representation: standard Heikin-Ashi only
journey: one contiguous same-color H4 HA run
entry: +1 fixed-size Child after each completed same-color H4 HA bar
maximum Children per Journey: 10
exit: first completed opposite-color H4 HA closes all Journey Children
reverse: after successful close-all, the same opposite HA starts the next Journey
Hard SL: none
TP: none
filters: none
ML: none
CRT / liquidity / Wave / session / news / MA / RSI / other indicators: none
```

A Baseline-0 comparison is invalid if any of those strategy semantics are
changed without naming a new V13 experiment.

## Canonical comparison window

The frozen comparison window for current V13 work is:

```text
2024-01-01 through 2026-08-28 available GOLD# history
```

Every claim that one V13 variant improves or worsens another must be based on
this entire window. A month, quarter, selected episode, or selected year may be
used for diagnosis only; it cannot replace the full-window comparison.

If the authoritative 2026 dataset is later extended, change the canonical end
only in an explicit authority update and rerun every comparator on the same new
full window.

## Research method

- Baseline 0 remains frozen and reproducible.
- Add or alter one strategy component at a time whenever possible.
- Keep entry, risk, participation, exit, and sizing changes separately
  attributable.
- Complexity is a cost. If the contribution of a component cannot be isolated,
  remove it rather than stacking more conditions on top.
- Do not invent hidden minimum-R, cooldown, retry, no-chase, direction-balance,
  time-of-day, or discretionary exceptions.
- Do not promote a rule from one or two attractive examples.
- Never inspect future prices before a decision. A stopped or closed Child is
  never resurrected from hindsight.

## Execution authority

MQL5 Strategy Tester on `Every tick based on real ticks` is the official V13
execution environment for baseline economic reports. Python/H4 next-open
reconstructions may be used as deterministic sanity checks, but they are not a
substitute for the tester report.

Baseline 0 intentionally has no SL or TP, so its main execution uncertainty is
market-order fill/close handling at H4 boundaries. The EA fails closed on a
trade-operation error rather than silently retrying or fabricating a fill.

## Historical generations

- V12 is the frozen immediate predecessor. CRT/HA/Wave/liquidity/ML research is
  retained as historical evidence only.
- V11 is frozen historical Wave/capital evidence.
- V10 is frozen historical HA/ML evidence and may be consulted only when a V13
  question explicitly needs historical comparison.
- V9 and earlier are historical evidence only.

No historical document overrides V13 authority.

## Repository hygiene

- Keep active V13 authority under `docs/ea/v13/`.
- Keep the frozen V13 baseline EA under `mt5/experts/`.
- Keep compact result receipts under `docs/ea/v13/results/`.
- Keep large tester exports and generated ledgers out of Git unless explicitly
  promoted to a compact receipt; Git history remains the archive.
- Record external ideas before they become V13 research hypotheses.
