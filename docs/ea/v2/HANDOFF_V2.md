# V2 Development Handoff

Last updated: 2026-08-22
Fork base: `123b41c880dbce2a17d560b4b7b081934d744700`
Current target build: `2.00R0L0 / V2_CONTINUATION_ONLY_BOOTSTRAP`
Current phase: **D-150 V2 CONTINUATION-ONLY FORK / LOCAL COMPILE + BOOTSTRAP VALIDATION PENDING**
V1: **FROZEN HISTORICAL CONTROL**
2021: **KEEP UNTOUCHED**

## Startup order

For active V2 work:

1. Check latest GitHub commit.
2. Read root `AGENTS.md` for project routing.
3. Read `docs/ea/v2/AGENTS_V2.md` as V2 strategy authority.
4. Read this file.
5. Read `docs/ea/v2/RESEARCH_STATE_V2.md` and `BACKLOG_V2.md`.
6. Read `docs/ea/D149_SP_EM_RESULTS_V1_AND_V2_PLAN.md`, D145, D146, D148 only as inherited research evidence.
7. Use V1 `EA_SPEC.md` only as historical lineage where V2 spec has not yet duplicated a rule.

## Why V2 exists

The project now deliberately focuses on trend-following continuation. Reversal performance has repeatedly failed to contribute enough value and currently distracts from the three problems that appear in both GOLD and BTCUSD:

```text
1. protect meaningful open profit without killing the large winner tail
2. distinguish a local +1R reaction from a true 2R+ runner
3. explain and solve genuine <1R Entry failures / clustered losses
```

## D149 evidence carried into V2

GOLD 2025 SP+EM V2 continuation:

```text
41 closed
22 wins
WR 53.66%
avg winner +1.515R
expectancy +0.331R/trade
total +13.555R
max DD 6.05R
longest nonpositive streak 3
```

The same all-scope run contained 7 reversal trades, 0 winners, about -7.40R. V2 removes that lane from strategy authority.

BTCUSD 2025 SP+EM V2 continuation, current right-censored run:

```text
63 closed continuation
25 wins
WR 39.68%
avg winner +1.137R
expectancy -0.163R/trade
total -10.262R
max DD 11.25R
longest nonpositive streak 7
```

The same run contained 19 closed reversals, 0 winners, about -19.68R, plus one unresolved continuation fill at tester end. The run is diagnostic, not final profitability evidence.

Cross-market positive SP evidence:

```text
GOLD: STRONG state materially outperformed DEFAULT for +2R continuation.
BTC: 7/7 closed STRONG trades reached the +2R protection stage.
```

Cross-market warning:

```text
+2R -> near-cost-BE can still surrender most open profit.
BTC Entry survival remains insufficient even when +1R survivors are converted to winners.
EM V2 helped GOLD drawdown/streak shape but showed a generalization warning on BTC because shadow setups were stronger than the real retained subset.
```

## Immediate next work

1. Apply D-150 package and compile V2.
2. Verify zero V2 reversal PLAN/fill/close events.
3. Re-run GOLD 2025 and BTCUSD 2025 under V2 continuation-only with SP V2 and EM OFF first.
4. Use those runs to isolate SP from EM and remove reversal contamination.
5. Before changing +2R protection, build a post-+2R retracement audit of true large winners.
6. Continue Entry-failure research separately; do not use the +1R runner variable as an Entry filter.

## D-151 active handoff

Current target build is now:

```text
2.01R0L1 / V2_CAUSAL_RESEARCH_PLATFORM_V1
```

The bootstrap fork itself has been validated on GOLD 2025 with zero reversal plans/fills/closes and clean execution. The next phase is not immediate threshold tuning. D-151 instruments the three continuation stages independently:

```text
Fill -> +1R
+1R -> +2R+
+2R -> tail continuation / giveback
```

Read `docs/ea/v2/D151_V2_CAUSAL_RESEARCH_PLATFORM.md` immediately after this handoff.

New project stretch target is `>=70%` cost-adjusted realized WR while preserving >1R average winner and positive expectancy, with `100% of accepted trades final net R >= +1R` retained as an extreme research frontier rather than a guarantee.
