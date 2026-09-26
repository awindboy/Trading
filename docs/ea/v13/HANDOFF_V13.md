# V13 handoff

Last synchronized: `2026-09-27`
Status: `BASELINE 0 FROZEN / HA-5 FIRST FIXED PROBE COMPLETE / HA-6 OBSERVATION NEXT`

## Resume point

V13 uses the simple EA as an observation instrument. HA-0..HA-5 research
receipts document morphology, lifecycle, four HA representations and D1/H1
context on the **same** Standard-H4 Journey. These are consumed development
evidence, not trading rules. HA-4C/D specifically repaired the earlier
color-heavy comparison scope; it did not prove a safe exit. HA-5 first fixed
probe confirmed actual raw-price swings causally and compared them with
ordered-H1 warnings and H4 morphology. It likewise did not prove a safe exit.

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

## Completed observation work — HA-0..HA-5

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
short-lived Journeys, or vice versa. HA-4: D1 alignment weakly separated
next-H4 flips (22.8% aligned versus 24.3% opposed); H1 opposition separated
them more (11.2% versus 47.3%) but 735 of 1,395 H1-opposed decisions did
not flip next H4 and all 88 long Journeys had at least one such warning.
Much of H1's pooled separation overlaps with H4 raw-close geometry. HA-4C/D
then separated H1 opposition that repaired within the H4 bar (16.1% next-H4
flip, 1,073 decisions) from opposition remaining at the end (46.6%-51.1%,
depending on its H1 path). However, H1's +36.1-point pooled opposition
contrast shrank to +13.1 or +4.4 points in different H4-morphology/raw-close
overlap bins, with incomplete coverage. All 88 long Journeys had at least one
H1-opposed warning, and 254 of their 318 warnings were not followed by a
next-H4 flip. PRE/POST EMA2 color identity hid 518 decisions with different
opposite-wick presence. No threshold or trade rule was promoted; see the
HA-4C/D receipt before interpreting HA-3 or HA-4 in isolation.

HA-5 rebuilt 7,198 H4 bars from 1,648,308 chronological M1 rows with zero
OHLC mismatches and classified 4,105 labeled Standard-H4 decisions against
previously confirmed actual-price swing levels. A fresh favorable close beyond
a swing had only 4.0% next-H4 reversals; a return inside a previously crossed
level had 64.7%. In last-H1-opposed decisions, favorable rejection/return
preceded 58.7% next-H4 reversals versus 45.0% otherwise, but this caught only
138/660 reversals, shrank after H4-morphology matching, and falsely warned in
long Journeys. No level state or numerical cutoff was promoted. Read
`results/V13_HA5_CAUSAL_RAW_SWING_RECEIPT_20260927.md` for scope and caveats.

## Immediate next work — HA-6 observation planning

The HA-5 first probe is complete as *description*. Do not turn its return-
inside or rejected-break states into an exit: within finer H4-morphology cells
there was no support for an independent claim, and 56/88 long Journeys had a
favorable rejection/return at some point. If revisiting raw swings, freeze a
distinct incremental question before measuring. Otherwise follow roadmap
HA-6 one complementary family at a time, observation first; begin by stating
which information that family adds beyond HA morphology, ordered H1 and
actual raw structure. No swing, D1, H1, FAST or EMA veto/exit is authorized.

HA-3's PRE-EMA2 and POST-EMA2 color sequences were identical under the stated
linear formulas. HA-4/5's warnings need false-warning and tail-preservation
accounting before any action experiment. The exact-window actual-tick
Baseline-0 receipt remains pending.

## Following order

Follow the roadmap. Do not jump directly to EMA/ADX/ML merely because
external sources combine them successfully in examples.
