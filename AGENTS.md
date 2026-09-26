# Trading repository authority

Last synchronized: `2026-09-27`
V13 HA-5 causal raw-swing observation base GitHub HEAD:
`1ab3e2e9dbe6bac0afe6223eef2f3fc3a936d4af`

## Active generation

V13 is the only active strategy-research generation.

V13 is a deliberate reset. It does not continue the V12 feature stack. It starts
from a minimal standard-Heikin-Ashi participation skeleton, studies Heikin-Ashi
itself before importing complexity, and adds one component at a time only after
its role is understood.

Start every V13 session in this order:

1. refresh GitHub `main`;
2. read `docs/ea/v13/AGENTS_V13.md`;
3. read `docs/ea/v13/V13_DOCUMENT_AUTHORITY_MAP_20260926.md`;
4. read `docs/ea/v13/HANDOFF_V13.md`;
5. read `docs/ea/v13/RESEARCH_STATE_V13.md`;
6. read `docs/ea/v13/V13_HA_KNOWLEDGE_AND_SOURCE_REGISTER_20260926.md`;
7. read `docs/ea/v13/V13_HA_RESEARCH_ROADMAP_20260926.md`;
8. read `docs/ea/v13/V13_BASELINE0_HA_MAX10_CONTRACT_20260926.md`;
9. read `docs/ea/v13/V13_EXECUTION_RECOVERY_20260926.md` and
   `V13_MQL5_BACKTEST_PROTOCOL_20260926.md` before tester/execution work;
10. read the current compact receipts under `docs/ea/v13/results/`, including
    HA-1 through the HA-5 causal raw-swing receipt;
11. inspect `mt5/experts/V13HAOnlyMax10EA.mq5` before changing implementation.

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

The frozen comparison window is:

`2024-01-01 through 2026-08-28 available GOLD# history`

Every primary V13 strategy comparison must use this entire window. A selected
month, quarter, year, or episode is diagnostic only.

## Current research doctrine

V13 treats Baseline 0 first as an **instrument for learning what standard
Heikin-Ashi actually represents**. HA-0..HA-5 are descriptive development
evidence. HA-5 added causally confirmed raw-price swing interactions to the
same Standard-H4 Journey, but did not establish robust incremental trade
authority beyond existing H4/H1 information. Read its compact receipt before
proposing any action rule; the next distinct roadmap stage is HA-6 observation.
The Baseline-0 EA and trading rules have not changed.

Research order is frozen in
`docs/ea/v13/V13_HA_RESEARCH_ROADMAP_20260926.md`.

Key rules:

- first extract more information from the same standard HA before adding another
  indicator;
- start with observation-only feature ledgers; no entry/exit rule changes;
- do not turn a descriptive threshold, quantile, Child number or side split into
  a trading rule merely because it looked attractive in consumed data;
- when an external component is tested, add one component at a time and state
  the distinct information it is supposed to contribute;
- source popularity is not evidence of edge;
- MQL5 Market/Forum/User Articles are hypothesis sources, not strategy authority;
- verify every imported HA formula against the MetaQuotes standard definition;
- keep decision-time inputs separate from future outcome labels;
- never inspect future prices before a historical decision timestamp;
- no hindsight recovery of stopped/closed Children.

## HA source authority

`V13_HA_KNOWLEDGE_AND_SOURCE_REGISTER_20260926.md` distinguishes:

1. platform/reference authority;
2. implementation/research examples;
3. academic evidence;
4. community/market practice leads;
5. external educational material.

No external source creates a V13 trading rule by itself.

## ML boundary

ML is a later research stage, not the next step. If reached, begin with causal
HA-state features and interpretable/tabular models before sequence models.
Preferred targets are lifecycle outcomes such as continuation, transition risk,
remaining favorable excursion, giveback and time-to-opposite-color rather than
a direct next-bar LONG/SHORT oracle.

Any ML pipeline must reproduce preprocessing identically in Python and MQL5;
ONNX transport does not excuse feature/preprocessing mismatch.

## Execution authority

MQL5 Strategy Tester on `Every tick based on real ticks` remains the official
execution environment for economic reports. Python/H4 next-open reconstruction
is a deterministic sanity check only.

Execution revision 13.002 retries explicit transient rejections, expires stale
entries, and resumes remaining closes without reversing early. Ambiguous or
permanent failures halt the run. This is execution recovery, not a strategy
cooldown/retry rule.

The uploaded extended tester report ending `2026-09-26` confirms structural
parity through the canonical source cutoff, but is not the official exact-window
receipt because its end date and leverage differ from the frozen tester protocol.
See the diagnostic receipt under `docs/ea/v13/results/`.

## Historical generations

- V12 is frozen historical CRT/HA/Wave/liquidity/ML evidence;
- V11 is frozen historical Wave/capital evidence;
- V10 is frozen historical HA/ML evidence and may be consulted only for an
  explicitly stated historical question;
- V9 and earlier are historical evidence only.

No historical document overrides V13 authority.

## Repository hygiene

- keep active V13 authority under `docs/ea/v13/`;
- keep the frozen V13 baseline EA under `mt5/experts/`;
- keep compact result receipts under `docs/ea/v13/results/`;
- keep large tester exports and generated ledgers out of Git unless explicitly
  promoted;
- register external research before converting it into a V13 hypothesis;
- retain raw source URLs and caveats in the source register.
