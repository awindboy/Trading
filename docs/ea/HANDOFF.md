# EA Development Handoff

Status: `ACTIVE V6 ROUTER`
Date: `2026-08-29`
Expected base HEAD for this documentation overlay: `8f9c6e3e03906f2e8b4c146c3b3bb4741f6ad0e2`
Active generation: `V6`
Current phase: `V6-003D ROLE-CONDITIONED CORE FREEZE / EXTERNAL VALIDATION PREP`
Production authority: `NONE`
Untouched reserve: `GOLD 2021`

## Startup order

1. Check latest GitHub HEAD.
2. Read root `AGENTS.md`.
3. Read this file.
4. Read `docs/ea/WORKFLOW_AND_ZIP_HANDOFF.md`.
5. Read `docs/ea/v6/AGENTS_V6.md`.
6. Read `docs/ea/v6/HANDOFF_V6.md`.
7. Read `docs/ea/v6/RESEARCH_STATE_V6.md`.
8. Read `docs/ea/v6/V6_003D_ROLE_CONDITIONED_CORE_FREEZE_RESULTS.md`.
9. Read `docs/ea/v6/DECISIONS_V6.md` and `BACKLOG_V6.md`.
10. Inspect exact code/data before changing strategy semantics.

GitHub is the Single Source of Truth. Chat history is only a workbench.

## Current authority summary

V6 research has moved beyond the conventional-indicator atlas and the exploratory event-source/FVG work. The current research control is a three-module role-conditioned architecture:

```text
DIRECTION / LOCAL QUALITY / DESTINATION

H:
DIRECT + D24 aligned + MENV HIGH_HIGH
-> existing 50% pullback Entry
-> +3R realize 25%
-> residual BE
-> +5R final

L1:
DIRECT + D14 = D24 = local direction
-> H-authorized parent excluded
-> market Entry
-> sweep-extreme SL
-> +1R or 4 active-hour cap

L2:
ONE_RENEG (+ -> - -> +, symmetric by direction)
+ D24 aligned
-> market Entry
-> sweep-extreme SL
-> +1R or 4 active-hour cap
```

Consumed 13-market-year core result:

```text
253 trades
WR 54.55%
avg positive +1.269R
EV +0.304R
net +76.96R
historical max DD about 9.37R
11/13 market-years positive
```

This is a `RESEARCH FREEZE`, not production promotion.

## Immediate next work

Do not continue consumed-panel rule invention by default.

Priority order:

1. acquire longer outcome-blind validation histories;
2. validate H/L core unchanged;
3. validate L2 D24-age hypothesis as shadow only;
4. use outcome-blind market-suitability descriptors before opening P/L;
5. build exact execution stress: spread, commission, slippage, swap;
6. reproduce in MT5 Strategy Tester / EA only after the offline architecture survives validation;
7. keep GOLD 2021 untouched until a final validation allocation is explicitly frozen.

Key market-suitability density descriptor currently under observation:

```text
atomic recovery -> valid M5 BOS trigger conversion rate
```

It strongly explains opportunity density, not profitability. Do not use it as a P/L filter.

## Closed exploratory routes

Do not silently reopen without a new causal formulation:

- conventional DMI/MACD/RSI/Aroon/Vortex rescue;
- nearby displacement-window tournaments;
- dropping direct-transfer merely to increase N;
- M5-liquidity / previous-H4 / pivot / FVG / opening-range source proliferation;
- accepted-breakout / delayed-failed-break families;
- generic pullback-resumption without liquidity event quality;
- H super-score / stronger-HH thresholding;
- H time-stop / early impatience rules;
- automatic opposed inversion;
- FVG research as an active branch.

Detailed evidence is in `docs/ea/v6/V6_003D_ROLE_CONDITIONED_CORE_FREEZE_RESULTS.md`.
