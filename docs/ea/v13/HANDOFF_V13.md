# V13 handoff

Last synchronized: `2026-09-27`
Status: `BASELINE 0 FROZEN / HA-0..HA-3 OBSERVATION COMPLETE / HA-4 NEXT`

## Resume point

V13 uses the simple EA as an observation instrument. HA-0..HA-3 research
receipts now document morphology, lifecycle, and four predeclared HA
representations. They are consumed development evidence, not trading rules.

The latest uploaded MT5 report is an extended real-tick run through
`2026-09-26`. Its canonical prefix confirms the intended Journey/Child structure:

```text
965 closed Journeys through the canonical source cutoff
3,858 Children inside those 965 closed Journeys
+ one open Journey (J966) beginning 2026-08-28 20:00
```

Those counts match the deterministic H4 sanity reconstruction. The report is
not the official exact-window economic receipt because it extends beyond
`2026-08-28` and used `1:500` leverage rather than the frozen protocol's `1:100`.
See the diagnostic receipt.

## Read first

1. refresh GitHub `main`;
2. read `AGENTS_V13.md`;
3. read the authority map and this handoff;
4. read `RESEARCH_STATE_V13.md`;
5. read `V13_HA_KNOWLEDGE_AND_SOURCE_REGISTER_20260926.md`;
6. read `V13_HA_RESEARCH_ROADMAP_20260926.md`.

## Baseline in one block

```text
standard H4 HA only
same-color run = Journey
one Child after every completed same-color H4 HA
maximum 10 Children
first opposite completed H4 HA = close all
same event then starts opposite Journey
1 fixed unit per Child
no SL / no TP / no filters / no ML
```

## What was learned conceptually

Do not overinterpret the current simple strategy.

The useful result is that it exposes HA behavior:

- smoothing creates long same-color persistence during directional moves;
- the same persistence delays reversal confirmation;
- later Children naturally enter farther along the move and can give back more
  before an opposite color appears;
- short choppy runs and long persistent runs are two manifestations of the same
  smoothing mechanism.

This is not authority to ban SHORTs, lower the ten-Child cap, or add a fixed
late-Child rule.

## Completed observation work — HA-0..HA-3

The Baseline-0 EA strategy remains unchanged. Decision ledgers record completed
H4 raw/HA OHLC, HA body/Delta/range/wick geometry, streak and Child index.
Separate future-label ledgers record raw M1 extrema, final Journey length,
exit/giveback and idealized no-cost Child price differences. These ledgers are
reproducible from `research/v13/ha_representation_audit.py` and stored locally;
compact source-backed findings are in `results/`.

HA-1: stronger HA body and clean opposite-wick morphology corresponded to
longer persistence, but are overlapping geometry, not two independent signals.
HA-2: median raw-extreme-to-exit lag was 7.35h and median giveback 21.41
GOLD price. HA-3: changing responsiveness exchanged shorter lag for more
short-lived Journeys, or vice versa. No threshold or trade rule was promoted.

## Immediate next work — HA-4

Observe D1 standard HA alongside the H4 baseline on the full canonical window.
Then study H1 standard HA separately around H4 transitions. Start with
decision-time state and future outcomes in separate ledgers. No D1/H1 veto,
score, or Baseline-0 trading action is authorized.

HA-3 found a clear responsiveness/persistence trade-off, not an economic
winner. Its PRE-EMA2 and POST-EMA2 color sequences were identical under the
stated linear formulas, so do not count them as independent color evidence.

## Following order

After HA-4, follow the roadmap. Do not jump directly to EMA/ADX/ML merely because
external sources combine them successfully in examples.
