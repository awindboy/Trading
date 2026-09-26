# V13 Research Instructions — Minimal HA Rebuild

Last synchronized: `2026-09-27`
Status: `ACTIVE / BASELINE 0 FROZEN / HA KNOWLEDGE PROGRAM ACTIVE / NO PRODUCTION AUTHORITY`
Market authority: `GOLD# ONLY`
Research-update base GitHub HEAD: `bc23a1dddeb79a62660367bed2382039c9871828`

## 0. Start order

GitHub `awindboy/Trading` latest `main` is the Single Source of Truth.

Read in this order:

1. repository `AGENTS.md`;
2. this file;
3. `V13_DOCUMENT_AUTHORITY_MAP_20260926.md`;
4. `HANDOFF_V13.md`;
5. `RESEARCH_STATE_V13.md`;
6. `V13_HA_KNOWLEDGE_AND_SOURCE_REGISTER_20260926.md`;
7. `V13_HA_RESEARCH_ROADMAP_20260926.md`;
8. `V13_BASELINE0_HA_MAX10_CONTRACT_20260926.md`;
9. `V13_EXECUTION_RECOVERY_20260926.md` and
   `V13_MQL5_BACKTEST_PROTOCOL_20260926.md` when execution/tester work matters;
10. `V13_HA3_REPRESENTATION_COMPARISON_CONTRACT_20260927.md`,
    `V13_HA4_MTF_OBSERVATION_CONTRACT_20260927.md`, `results/README.md`,
    and the HA-1..HA-4 receipts;
11. `../../../mt5/experts/V13HAOnlyMax10EA.mq5` for implementation parity.

## 1. Why V13 exists

V13 intentionally resets the strategy stack after V9-V12 accumulated too many
interacting components to attribute gains and failures cleanly.

The V13 question is:

> How far can a minimal standard-HA participation engine go, what does HA itself
> actually encode, where does it lag or discard information, and what single
> addition improves a demonstrated weakness without obscuring the cause?

Do not reconstruct an old strategy and do not automatically import old rules.
Historical generations may explain prior failures, but V13 rules must be earned
again from the V13 baseline.

## 2. Frozen Baseline 0

Baseline 0 uses only standard H4 Heikin-Ashi.

```text
HA_CLOSE = (O + H + L + C) / 4
HA_OPEN(first warm-up bar) = (O + C) / 2
HA_OPEN(t) = (HA_OPEN(t-1) + HA_CLOSE(t-1)) / 2
HA_HIGH = max(raw H, HA_OPEN, HA_CLOSE)
HA_LOW  = min(raw L, HA_OPEN, HA_CLOSE)
```

Baseline trading color:

```text
BULL if HA_CLOSE > HA_OPEN
BEAR if HA_CLOSE < HA_OPEN
exact equality inherits the previous non-zero color
```

Journey / Child semantics:

```text
one contiguous same-color completed-H4 HA run = one Journey
first qualifying HA flip starts Child #1
next completed same-color HA bar adds Child #2
...
maximum = 10 successful Children
bars after Child #10 add nothing
first completed opposite-color H4 HA closes all Journey Children
same opposite-color event starts the next Journey after close-all succeeds
```

No Hard SL, TP, break-even, trailing, partial TP, liquidity, CRT, Wave, ML,
session, news, volatility gate, MA, oscillator or dynamic sizing exists in
Baseline 0.

## 3. What the first actual-tick run changed conceptually

The extended actual-tick tester report confirms that the repaired EA follows the
intended Journey/Child structure through the canonical source cutoff. It does
not justify optimizing Child count, banning SHORTs, or adding filters.

The important interpretation is simpler: the baseline exposes known HA
properties clearly. Same-color persistence captures long directional moves;
synthetic smoothing delays reversal recognition; late Journey entries naturally
see more giveback before an opposite color is confirmed.

V13 therefore studies **HA as a representation** before treating Baseline 0 as a
finished strategy to optimize.

## 4. Causal timing

Only completed H4 bars may decide.

At the first executable tick after a new H4 bar opens:

1. the just-completed H4 raw OHLC is known;
2. its standard HA OHLC is finalized;
3. any research features for that timestamp are frozen;
4. the Baseline-0 Journey decision is made;
5. orders execute on real market Bid/Ask, never on synthetic HA prices.

Warm-up history before 2024 initializes recursive HA state only. It cannot carry
an old position into the evaluation window.

## 5. Comparison-window authority

Canonical window:

`2024-01-01 through 2026-08-28 available GOLD# history`

Every primary V13 strategy comparison uses the entire window. Year/month/episode
slices diagnose mechanisms only.

## 6. HA research authority

The current source-backed HA map is
`V13_HA_KNOWLEDGE_AND_SOURCE_REGISTER_20260926.md`.

The ordered experiment program is
`V13_HA_RESEARCH_ROADMAP_20260926.md`.

Neither document adds a trading rule. They define what may be measured and in
what order hypotheses are investigated.

The immediate priority is standard-HA internal information:

- HA Delta (`HA_CLOSE - HA_OPEN`);
- body size and body/range strength;
- HA upper/lower wick geometry;
- directional versus opposite wick;
- no-opposite-wick state;
- same-color streak/persistence;
- body/Delta expansion and contraction;
- raw-price versus HA displacement;
- lag from raw-price turning points to HA color transition.

These are observations before they are rules.

## 7. External-source boundary

MetaQuotes platform/reference semantics outrank community formulas.

MQL5 Articles, CodeBase contributions, Forum discussions, Market products,
external educational pages and academic papers can suggest measurements or
combinations. They do not receive action authority merely because they exist or
report a profitable backtest.

Before using an imported HA implementation:

1. verify its formula against the standard recursive HA definition;
2. identify whether smoothing is applied before HA, after HA, or both;
3. verify completed-bar/no-repaint timing;
4. separate synthetic HA values from executable raw Bid/Ask prices;
5. record parameter provenance rather than silently optimize it.

## 8. Research discipline

- Baseline 0 stays frozen.
- First measure; then form a mechanism hypothesis; only then test one rule.
- Add one component at a time whenever possible.
- Do not infer that late Child underperformance means a fixed Child cap should be
  reduced. Late-child giveback is first treated as evidence about HA lag.
- Do not infer a side ban from pooled LONG/SHORT results. Tail structure must
  remain visible.
- Do not mine a threshold, cooldown, minimum-R, no-chase distance, session gate,
  or direction quota from consumed data and silently call it a rule.
- Keep decision fields and future outcomes physically separable.
- Never inspect future prices before a historical decision timestamp.
- A closed Child stays closed; hindsight never resurrects it.

## 9. ML boundary

ML is deliberately late in the roadmap.

If reached, begin with causal HA-state features and simple/interpretable models
(logistic/regularized linear baselines, then tree models) before LSTM/TCN/
Transformer-style sequence models.

Preferred research targets are lifecycle outcomes, for example:

- probability the current HA color survives another `k` bars;
- transition hazard to the opposite color;
- remaining favorable excursion before the flip;
- giveback from future peak to eventual HA exit;
- time to opposite-color confirmation.

The future may define an outcome label **after** decision-time features are
frozen; it may never leak into the feature vector.

Any Python model promoted toward MT5 must reproduce the complete preprocessing
path in MQL5 and pass vector/output parity before economic claims. ONNX is a
transport format, not a substitute for preprocessing parity.

## 10. Execution boundary

Official economics come from MT5 Strategy Tester with `Every tick based on real
ticks`.

Execution revision 13.002 follows
`V13_EXECUTION_RECOVERY_20260926.md`. Explicit transient rejections may recover;
ambiguous/permanent failures invalidate the run.

The current uploaded report is an extended diagnostic run, not the official
exact-window receipt, because it ends after the frozen cutoff and uses different
leverage from the frozen protocol.

## 11. Current next action

HA-0..HA-4 descriptive work is recorded in compact receipts. HA-4 studied
D1 and H1 separately. D1's next-H4 separation was weak; H1 opposition was
strongly associated with transition but issued many false warnings and
overlapped with H4 raw-close geometry. No MTF veto or exit was promoted.
Begin HA-5 raw-price structure as observation only.

The exact-window MT5 rerun should still be captured before any strategy variant
is promoted economically, but it does not block observation-only HA measurement.
