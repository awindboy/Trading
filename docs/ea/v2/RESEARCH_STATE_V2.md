# V2 Research State

Last updated: 2026-08-24  
Phase: `D-154O BROAD-MARKET GOLD-LIKE EXECUTION-SUITABILITY SCREEN`  
Current tested EA: `2.11R0L11 / D154M`  
Execution environment: `XM Ultra Low`  
D154N: `DEFERRED`  
Authority: `docs/ea/v2/AGENTS_V2.md`  
2021: `KEEP UNTOUCHED`

## Primary objective

Build a robust continuation strategy with:
- realized WR >=50% as a baseline condition;
- average winner meaningfully >1R;
- positive cost-adjusted expectancy;
- persistence across periods and compatible markets.

Do not require one strategy to work on every tradable symbol if a causal market-compatibility condition exists.

## Axis A — Fill -> +1R Entry survival

Status:

```text
PRIMARY BOTTLENECK
+
MARKET EXECUTION-SUITABILITY HYPOTHESIS UNDER BROAD VALIDATION
```

Ultra Low 2025:

```text
GOLD#      58.2%
BTCUSD#    48.8%
SILVER#    38.3%
CADJPY#    30.1%
```

D154A-J eliminated several universal timing/HTF geometry gates.

D154K/L/M/UL support:

```text
lower execution friction relative to local strategy geometry
-> better probability that Entry edge survives across markets
```

This remains a market/environment relation, not a per-trade spread gate.

## D154O question

Does the relation generalize to a much broader Ultra Low symbol universe?

Two stages:

```text
Stage A:
fixed one-week chart-only / outcome-blind raw screen

Stage B:
frozen shortlist + controls
-> 2025 real-tick strategy confirmation
```

## Stage-A governance

Frozen week:

```text
2026-08-17 .. 2026-08-23
```

Do not use one-year strategy outcomes during screening.

Raw chart metrics are proxies and must not be mislabeled as exact D154K:
- raw spread / M1 TR;
- raw spread / generic M1 FVG;
- spread bps;
- distribution/data quality.

GOLD# same-week data is the reference.

No weighted score.

## Stage-B governance

Freeze shortlist/control manifest before outcomes.

Then run exact:
- D151;
- D154K;
- D154M;
- current V3E reference.

Report sample size and direction.

Do not promote a tiny-sample high WR market.

## Temporal validation

If 2025 broad-market results support the hypothesis, use another disjoint year before permanent market eligibility authority.

## Axis B — +1R -> +2R winner continuation

Separate problem.

Lower M30 protected-to-external progress at +1R remains the strongest descriptive continuation relationship. It is not an Entry or market screen variable.

## Axis C — exit architecture

V3E `BANK_2R_LOCK_ONE` remains the provisional post+1R reference.

Do not use D154O to optimize exit rules.

## D154N

Pre-Fill pending quote-delay/depth audit remains scientifically valid but is deferred.

Resume only after D154O interpretation if still strategically useful.
