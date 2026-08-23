# V2 Development Handoff

Last updated: 2026-08-24  
Git HEAD before this local phase update: `0b317facba97f4edc305d0d4c82fbe5bd10a9739`  
Current tested EA: `2.11R0L11 / V2_D154M_EXECUTION_FRICTION_COUNTERFACTUAL`  
Current execution environment: **XM Ultra Low**  
Current phase: **D154O STAGE B 2025 FROZEN-COHORT STRATEGY CONFIRMATION — ACTIVE**  
D154N: **DEFERRED / NOT REJECTED**  
V1: **FROZEN HISTORICAL CONTROL**  
2021: **KEEP UNTOUCHED**

GitHub is the Single Source of Truth. This handoff is intended to be committed before the next ChatGPT session.

## Startup order for the next session

1. Check latest GitHub commit.
2. Read root `AGENTS.md`.
3. Read `docs/ea/v2/AGENTS_V2.md`.
4. Read root `docs/ea/HANDOFF.md`.
5. Read this file.
6. Read `docs/ea/v2/RESEARCH_SYNTHESIS_D154A_D154UL.md`.
7. Read `docs/ea/v2/D154UL_ULTRA_LOW_EXECUTION_ENVIRONMENT_RESULTS.md`.
8. Read `docs/ea/v2/D154O_BROAD_MARKET_GOLD_LIKE_SCREEN.md`.
9. Read `docs/ea/v2/D154O_STAGE_A_UNIVERSE_MANIFEST.md`.
10. Then inspect `RESEARCH_STATE_V2.md`, `BACKLOG_V2.md`, and current code.
11. Do **not** start D154N unless D154O is explicitly closed or deprioritized.

## Strategy authority

Unchanged:

```text
EXTERNAL_CONTINUATION only
BASELINE_NO_REGIME_GATE
ROOT_OB_DISTAL_20
LAST_OPPOSITE_OB + FVG_ORIGIN_OB
PD = reference only
same-entry Root merge
same-direction add-ons
opposite-direction coexistence blocked
no look-ahead
```

No D154A-UL result has authorized:
- a new Entry gate;
- a spread threshold;
- a symbol veto;
- SL widening;
- FVG widening;
- TP/sizing/SP/EM changes.

## Research-stage separation

Keep separate:

```text
Fill -> +1R       = Entry survival
+1R -> +2R        = winner continuation
post +2R          = exit architecture
execution         = broker / quote mechanics
market universe   = environment compatibility
portfolio         = exposure risk
```

## Current Entry-survival evidence

Standard-account 2025:

```text
          spread/reactionTR   spread/1R   spread/FVG   Entry survival
GOLD            0.342          0.028       0.462         56.6%
BTC             1.015          0.063       1.026         47.2%
SILVER          1.701          0.147       2.099         39.1%
CADJPY          2.125          0.150       2.688         26.5%
```

Ultra Low 2025:

```text
          spread/reactionTR   spread/1R   spread/FVG   Entry survival
GOLD#           0.162          0.014       0.247         58.2%
BTCUSD#         0.541          0.032       0.551         48.8%
SILVER#         1.303          0.108       1.500         38.3%
CADJPY#         1.631          0.124       2.056         30.1%
```

The market-level cost-scale relationship has survived:
- D154K discovery contrast;
- D154L cross-market validation;
- D154M direct post-Fill quote counterfactual;
- D154UL account/feed natural experiment.

## D154M / D154UL causal evidence

Standard D154M actual SL-first -> entry-side quote +1R flips:

```text
GOLD       1
BTC        7
SILVER     0
CADJPY    17
```

Ultra Low:

```text
GOLD#       0
BTCUSD#     3
SILVER#     0
CADJPY#    10
```

Lower Ultra Low spread reduced the direct quote-side flip mechanism where it existed.

Exact Standard/Ultra scenario overlap:

```text
GOLD      common 48
BTCUSD    common126
SILVER    common 43
CADJPY    common112
```

Across 329 common scenarios:

```text
SL_FIRST -> PLUS_1R = 7
PLUS_1R -> SL_FIRST = 0
```

Interpretation:
- execution friction is causal;
- execution friction is only a partial cause;
- Ultra Low does not rescue high-friction markets enough to solve Entry survival.

## Strategic pivot

The highest-value question is no longer:

> How can the same strategy be forced to trade every high-friction market well?

The active question is:

> Does the current V2 strategy reproduce GOLD-like performance across a broader set of markets whose execution scale is naturally GOLD-like?

If yes, a compatible market universe may be more valuable than increasingly complex rescue logic for CADJPY/SILVER-like environments.

## D154O Stage A — outcome-blind one-week raw screen

The broad primary Stage-A universe is now frozen before new-symbol outcomes:

```text
Universe ID: D154O_STAGE_A_UL32_20260824
Forex:       15
Crypto:       8
Spot Metals:  9
TOTAL:       32
Reference:   GOLD#
```

Exact symbol list and exclusion rationale:

`docs/ea/v2/D154O_STAGE_A_UNIVERSE_MANIFEST.md`

The initially considered US Stocks cohort (`Nvidia`, `Nasdaq`, `Apple`, `Google`) is excluded because the broker's `Stocks/US` category has no Ultra Low classification. The exclusion was made before Stage-A/new-symbol 2025 outcomes and is an execution-environment compatibility decision, not a performance screen.

Frozen raw-screen window:

```text
2026-08-17 00:00
through
2026-08-23 23:59
broker/server time
```

Collect the same week for every symbol.

Preferred minimum data:
- M1 OHLC;
- spread in points;
- symbol point/digits;
- tick volume if available.

Do not require a strategy trade.

Do not inspect one-year win rate or P/L.

Raw screen must clearly distinguish proxies from exact D154K metrics.

Primary raw proxy:

```text
median spread_price / median valid M1 true range
```

Secondary raw proxy:
- spread / generic all-M1-FVG width;
- spread / close price in bps;
- daily stability / quantiles;
- data-quality diagnostics.

GOLD# from the same week is the reference.

Report every market relative to GOLD#.

No combined weighted `GoldLikeScore`.

### Stage-A infrastructure prepared

Standalone research collection is prepared without modifying the strategy EA:

```text
mt5/scripts/D154OStageAExporter.mq5
config/d154o_stage_a_universe.json
tools/install_d154o_stage_a_exporter.py
tools/summarize_d154o_stage_a.py
```

The exporter:
- runs as an MT5 Script, not the V2 strategy EA;
- uses the fixed server-time window;
- exports all 32 M1 datasets to MT5 Common Files;
- records M1 OHLC, stored spread points, point/digits and tick volume;
- records broker `SYMBOL_PATH` so Ultra Low classification can be checked;
- writes an explicit `EXPORT_COMPLETE` only for 32/32 success.

The summarizer is fail-closed on incomplete universe/path/time-window mismatches and produces only chart proxies/data quality. It does not read or generate strategy outcomes.

Local MetaEditor compile and actual MT5 export have **not** yet been validated and remain the next task.

## D154O shortlist freeze

After Stage-A raw metrics are computed:

1. inspect only execution-scale/data-quality results;
2. define and save the `Gold-like shortlist manifest`;
3. define and save a small non-Gold-like negative-control cohort;
4. freeze both before any one-year strategy outcome is produced.

The shortlist rule may use the observed **execution-metric distribution** because outcomes are still hidden. The final rule and rationale must be saved before Stage B.

Do not add/drop markets after their one-year outcome is known.

## D154O Stage B — 2025 strategy confirmation

Run:

```text
XM Ultra Low
Every tick based on real ticks
2025-01-01 .. 2025-12-31
```

for:
- all frozen Gold-like candidates;
- frozen negative controls.

Use current strategy semantics and:
- V3E mode 9;
- EM OFF;
- D151 ON;
- D154K ON;
- D154M ON.

Report:
- Fill count;
- Fill->+1R survival;
- LONG/SHORT survival;
- exact D154K spread/reactionTR;
- exact D154K spread/1R;
- exact D154K spread/selected-FVG;
- D154M shadow survival and flip rate;
- realized V3E WR, average winner R, expectancy R as separate strategy-level evidence.

Tiny samples are `INSUFFICIENT_STRATEGY_SAMPLE`, not success.

## D154O interpretation

### If Gold-like markets generally reproduce good survival

Prioritize future strategy research on the compatible universe.

Do not spend primary research effort forcing very high-friction markets to work.

### If Gold-like markets are mixed/poor

Cost scale is helpful/necessary but insufficient.

Return to underlying market regime / path-quality research within the low-friction cohort.

### If the broad universe breaks the relationship

Do not build a market-eligibility architecture from D154K-L-M-UL.

## Temporal confirmation

A successful 2025 cross-market result is not yet permanent strategy authority.

Before a production market-eligibility layer:
- use an additional disjoint year where data exists;
- keep the frozen selection logic;
- confirm the relationship does not reverse.

## D154N disposition

D154N pending->opposite quote touch->executable quote touch->Fill delay/depth is:

```text
DEFERRED
not rejected
not deleted
```

Resume only if D154O fails to produce a viable compatible market cohort or if later execution research specifically needs it.

## Immediate next task

```text
1. apply the D154O Stage-A infrastructure package to Git HEAD 0b317fac...
2. run tools/install_d154o_stage_a_exporter.py
3. require MetaEditor compile = 0 errors in the exact active XM terminal
4. run D154OStageAExporter once in MT5
5. require EXPORT_COMPLETE = 32/32
6. run tools/summarize_d154o_stage_a.py
7. inspect the complete outcome-blind GOLD-relative screen
8. freeze Gold-like shortlist + negative controls
9. only then create one-year backtest batch
```

No 2025 strategy outcomes for new symbols should be generated before step 8.

## Infrastructure note

`mt5_batch_runner.py` uses the EX5 selected in the active MT5 AppData data directory.

Whenever the strategy EA is later modified:
- synchronize the repo MQ5 to the exact runner-selected terminal source;
- compile that exact source;
- verify the runner EX5 SHA changed.

D154O Stage A does not modify `MentorDeterministicV2EA.mq5`. Its standalone exporter has its own terminal source/EX5 and compile-state record.


## D154O Stage A completion / Stage B freeze — 2026-08-24

Stage A is complete. Read `D154O_STAGE_A_RESULTS_AND_STAGE_B_FREEZE.md` before
running or interpreting any new 2025 symbol result.

Frozen Stage-B cohort:

```text
REFERENCE
GOLD#

GOLD_LIKE
XAUJPY#
XAUCNH#
BTCUSD#
XAUEUR#
GAUCNH#
GAUUSD#
USDJPY#

NEGATIVE_CONTROL
GBPUSD#
SILVER#
EURUSD#
ETHUSD#
```

Immediate next task:

```text
python tools\run_d154o_stage_b_2025.py
```

The script is fail-closed to Git HEAD `0b317facba97f4edc305d0d4c82fbe5bd10a9739` and the frozen 12-symbol
manifest. Upload `D154O_STAGE_B_2025_RESULT.zip` after completion.

Do not run D154N and do not alter the shortlist after seeing Stage-B outcomes.
