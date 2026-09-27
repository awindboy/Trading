# V13 Research Instructions — Minimal HA Rebuild

Last synchronized: `2026-09-28`
Status: `ACTIVE / BASELINE 0 FROZEN / HA-7 REJECTED / HA-8A COMPLETE / X1-X2 DOLLAR PROXIES NEGATIVE / NO PRODUCTION AUTHORITY`
Market authority: `GOLD# ONLY`
GitHub SSOT base HEAD checked for this update: `53457bf5a38b0da0b77da094b6ea0223bc238fab`

## 0. Start order

GitHub `awindboy/Trading` latest `main` is the Single Source of Truth. On a new
session, refresh `main` first. If a later GitHub commit conflicts with this local
package, the later GitHub authority wins.

Read V13 in this order:

1. repository `AGENTS.md`;
2. this file;
3. `V13_DOCUMENT_AUTHORITY_MAP_20260926.md`;
4. `HANDOFF_V13.md`;
5. `RESEARCH_STATE_V13.md`;
6. `V13_HA_KNOWLEDGE_AND_SOURCE_REGISTER_20260926.md`;
7. `V13_HA_KNOWLEDGE_AND_SOURCE_REGISTER_ADDENDUM_20260927.md`;
8. `V13_HA_RESEARCH_ROADMAP_20260926.md`;
9. `V13_HA_RESEARCH_ROADMAP_STATUS_ADDENDUM_20260927.md`;
   then `V13_HA_RESEARCH_ROADMAP_STATUS_ADDENDUM_20260928.md`;
10. `V13_BASELINE0_HA_MAX10_CONTRACT_20260926.md`;
11. `V13_EXECUTION_RECOVERY_20260926.md` and
    `V13_MQL5_BACKTEST_PROTOCOL_20260926.md` before tester/execution work;
12. the named HA-3..HA-7 contracts, especially the HA-6A/B/C/D1/E and HA-7
    contracts added on `2026-09-27`;
13. `V13_HA6_HA7_RESEARCH_SYNTHESIS_20260927.md`;
14. `results/README.md` and the compact receipts through HA-7;
15. `V13_HA8A_COMBINATION_MODEL_CONTRACT_20260928.md` and its result receipt
    for the completed first HA-8A model diagnostic;
16. `../../../mt5/experts/V13HAOnlyMax10EA.mq5` before any implementation change.
17. `V13_X1_ECB_DOLLAR_OBSERVATION_CONTRACT_20260928.md` and its result
    receipt for the later, separate external daily-proxy observation.
18. `V13_X2_MT5_EURUSD_H4_OBSERVATION_CONTRACT_20260928.md` and its result
    receipt for the separate, same-broker H4 bilateral-FX observation.

## 1. Frozen Baseline 0 remains unchanged

V13 still starts from one decision source: completed standard H4 Heikin-Ashi.

```text
HA_CLOSE = (O + H + L + C) / 4
HA_OPEN(first warm-up bar) = (O + C) / 2
HA_OPEN(t) = (HA_OPEN(t-1) + HA_CLOSE(t-1)) / 2
HA_HIGH = max(raw H, HA_OPEN, HA_CLOSE)
HA_LOW  = min(raw L, HA_OPEN, HA_CLOSE)
```

Color:

```text
BULL if HA_CLOSE > HA_OPEN
BEAR if HA_CLOSE < HA_OPEN
exact equality inherits previous non-zero color
```

Journey / Child semantics:

```text
one contiguous same-color completed-H4 run = Journey
first qualifying flip starts Child #1
one further Child after each completed same-color H4
maximum 10 successful Children
first opposite completed H4 closes all Journey Children
same opposite event then starts the opposite Journey after close-all
1 fixed unit per Child
```

No Hard SL, TP, break-even, trailing, partial close, liquidity rule, CRT, Wave,
ML action, session gate, news gate, volatility gate, MA filter, oscillator filter
or dynamic sizing is part of Baseline 0.

## 2. Causal timing and data discipline

Only completed bars may decide. At the first executable print after a new H4
bar opens, the just-completed raw H4 and its research features become available.
Synthetic HA values are never executable prices.

Canonical comparison window remains:

`2024-01-01 through 2026-08-28 available GOLD# history`

2022 history is warm-up/state only. No position carries from pre-2024 history.
Future labels may be computed only after decision-time features are frozen.
Never inspect future price before a historical decision timestamp, never add a
hindsight trade after an accidental reveal, and never resurrect a stopped/closed
Child using later information.

## 3. Research discipline remains binding

- Baseline 0 stays frozen unless a separately named action contract is promoted.
- Measure first, identify a mechanism second, test one action third.
- Add one information family at a time whenever possible.
- Do not infer a fixed Child cap, side ban, late-Child ban, minimum-R, cooldown,
  retry limit, fixed no-chase distance, session gate or threshold from a small
  number of examples.
- Quantiles are descriptive display bins unless a later contract explicitly
  freezes a semantic boundary before economic measurement.
- Keep full-window, year/side and long-Journey tail diagnostics visible.
- Stronger reversal probability does not by itself justify an exit or Child
  veto; payoff asymmetry and right-tail preservation must be measured.

## 4. Consumed HA knowledge through HA-7

HA-0..HA-6 are consumed observation research. HA-7 tested one frozen action and
was rejected. None changes Baseline 0.

Key result by stage:

- **HA-1 morphology**: body/Delta/wick geometry contains persistence and
  transition information, but the variables overlap strongly.
- **HA-2 lifecycle**: standard HA preserves trends but creates measurable turn
  lag and giveback; median raw-extreme-to-exit lag was 7.35h and median giveback
  21.41 GOLD price on the consumed sample.
- **HA-3 representations**: faster/smoothed representations mostly trade lag
  against switching frequency; no representation earned strategy authority.
- **HA-4 MTF**: D1 adds little; H1 opposition is informative but produces many
  false warnings, including inside all 88 long Journeys.
- **HA-5 raw swing**: causal raw-price swing rejection/return adds some context
  but does not safely distinguish temporary weakness from true transition.
- **HA-6A HASTOC10**: strong pooled ordering survives only modestly after prior
  state matching; weak HASTOC remains unsafe as an exit.
- **HA-6B moving averages**: EMA50 provides slower regime context and EMA20
  envelope provides extension context, but both falsely warn in long Journeys.
- **HA-6C ATR**: useful as a volatility-aware coordinate, not as a signal. Raw
  GOLD price-unit features drift strongly across years; ATR normalization
  removes most scale drift. Existing trailing-20-H4 range normalization remains
  at least as good for lifecycle outcomes.
- **HA-6D1 ADX/DMI**: ADX strength is distinct but weak/unstable; DMI mostly
  re-expresses HA-6B raw-price trend context; ADX falling adds almost no
  independent information after the full prior state stack. HA-6D stop condition
  is met; SuperTrend was not tested or judged.
- **HA-6E tick volume**: absolute tick counts drift by year/session. Same-slot
  trailing-20 relative tick volume is stable enough for research. Universal
  low-volume separation is largely H4 morphology redundancy. A narrower
  persistent-H1-opposition + above-normal-participation interaction survived as
  a mechanism candidate, but still had major tail false warnings.
- **HA-7 first action**: suppressing one add-on Child on continuation bars when
  `persistent_opposition AND relative_tick_volume20 > 1.0` removed 89 Children
  and worsened net points by 77.93 while worsening realized-Journey DD by 30.91.
  It removed +341.09 points from 15 Children inside long Journeys. **Rejected.**

Read the named receipts for exact denominators, overlaps and caveats.

## 5. Current research interpretation

Multiple independent-looking warnings repeatedly converge on the same failure:

> A state can have elevated near-term reversal hazard while the minority
> continuation outcomes still contain economically dominant right-tail value.

Therefore V13 has not earned a deterministic exit/filter/veto rule from HA-0..
HA-7. The research problem is now conditional state discrimination, not another
single-indicator threshold search.

## 6. HA-8A first causal lifecycle state-model diagnostic

HA-8 remains **observation/model evaluation only**, not a trading-rule change.
The first frozen target was:

`P(opposite standard-H4 HA color within the next 3 completed H4 bars)`

The roadmap's complexity ladder was:

1. constant/base-rate predictor;
2. regularized logistic regression;
3. shallow tree / small Random Forest only if the linear baseline leaves a
   repeatable nonlinear residual;
4. XGBoost/CatBoost only if justified later;
5. sequence models only after tabular baselines are understood.

The first HA-8A run stopped at constant/single-family references and
regularized logistic regression. No tree, boosted or sequence model was run;
the additive residual was too small and unstable to justify one.

Candidate decision-time features come only from already measured causal state:
H4 HA morphology, ordered H1 path, HA-5 raw structure, HASTOC10, MA context,
ATR-normalized coordinates, ADX/DMI and normalized tick participation.

Because 2024-2026 is consumed development history:

- use chronological walk-forward/out-of-fold predictions;
- never report in-sample model predictions as strategy performance;
- keep year/side/Journey/tail diagnostics;
- do not choose a trading threshold from the same OOF predictions and call it
  production evidence;
- untouched future data is required for strong promotion claims.

The first HA-8A combination ladder (H4/H1, HASTOC, same-slot tick activity,
causal raw swing, EMA50) was evaluated on 3,338 chronological OOF decisions.
H4+H1 Brier was `0.22608`; the best expanded Brier was only `0.22530`.
Among 471 highest-risk OOF add-on Children under the activity model, 287 lost
and 184 won, yet the group contributed `+513.61` idealized price points.
Profitable long-Journey Children remained false transition warnings. The
result is **NO ACTION / NO MODEL PROMOTION**; read the 2026-09-28 receipt for
fold stability, economic decomposition and limitations.

X1 subsequently tested a distinct economic-Journey-loss target at Child #1
using a two-broker-calendar-day-lagged official ECB daily EUR/USD proxy. Across
777 chronological OOF Journeys, adding the proxy worsened Brier `0.18706 ->
0.18888`, did not concentrate repeat losses, and flagged more large winning
Journeys. **Negative result for this daily bilateral proxy / NO ACTION.** It
does not test a true intraday dollar index or negate all external information.

X2 then obtained clock-matched `EURUSD#` H4 from the same MT5 broker; all
7,199 GOLD# H4 timestamp/OHLC bars matched the frozen source and all had FX
bar coverage. Yet on 777 chronological OOF Journey births, H4/H1 loss Brier
`0.18706` worsened to `0.18810` with FX changes and `0.18865` with a
side-alignment interaction, in all four blocks. Top-risk bucket loss counts
did not improve and long-Journey false warnings increased. The broker's
`USDX-DEC26` old-looking history was rejected because the symbol start_time
is after the cutoff. **No external action or EA authority.**

If continuing HA-8, first freeze a distinct economic-lifecycle target and
explicitly test repeated losing Journeys versus large continuation winners.
Do not mine a threshold or retroactively reframe this first target as profit.

## 7. Execution boundary

Official economics still require MT5 Strategy Tester `Every tick based on real
ticks` under the frozen protocol. The exact-window official Baseline-0 economic
receipt is still pending. The existing extended run confirms structural parity
but uses a later end date and 1:500 leverage instead of the frozen 1:100 setup.

No HA-6/HA-7/HA-8A result changes the EA. If an HA-8 model ever affects action, Python
and MQL5 preprocessing/vector/output parity must be demonstrated before tester
economics.
