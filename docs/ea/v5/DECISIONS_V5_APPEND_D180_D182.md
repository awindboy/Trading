# V5 Decisions D-180 through D-182

Date: `2026-08-27`

## D-180 — Supersede the final payoff objective

Status: `ACTIVE`

The prior V5 gate (`WR >=50%, avg positive >1R, EV >0`) is insufficient for final promotion.

New final economic requirement:

```text
realized positive-trade rate >= 50%
average positive NET R       >= 2.0R
cost-adjusted expectancy     > 0
```

`2R` is a performance criterion, not a fixed 2R take-profit rule.

A promoted candidate must also survive independent markets/periods and must not obtain the mean from an implausibly tiny
winner tail.

## D-181 — Reclassify V5-030A and stop V5-034A promotion work

V5-030A remains:

```text
HISTORICAL DEVELOPMENT PASS UNDER SUPERSEDED GATE
```

Under D-180 it is:

```text
FINAL ECONOMICS FAIL
```

because average positive net R is about `1.197R`.

The frozen V5-034A external validation is no longer a promotion path for this candidate.
Do not consume GOLD# 2021.

The supplied XAUJPY#/XAUCNH#/GAUCNH#/GAUUSD# broker-symbol histories begin only around September 2025, so the original
2023-2025 V5-034A window is not executable on those exact histories. This is data/symbol-history infeasibility, not a
formal validation FAIL.

Any short-window inception diagnostic remains non-authoritative.

## D-182 — No First Cross rescue mining; test continuation-mechanism portability first

V5-035A/B/C show:

- real 2R+ excursion exists;
- partial-fraction tuning cannot satisfy the new joint WR/payoff objective;
- same-240m structural trailing is not a supported simple rescue;
- original slow/fast/EMA state is not broadly stable enough for a new rule.

Do not continue threshold/partial/trailing mining.

Before abandoning the useful First Cross Entry-survival result entirely, test one higher-level hypothesis already
supported in the older V3 architecture:

```text
D-145:
among +1R survivors, lower M30 protected->external maturity
was associated with +2R continuation across
6/6 market-year aggregates and 11/11 comparable direction cells.
```

This variable may NOT be automatically transferred into V5.

First determine whether the D-145 M30 state is genuinely Entry-architecture-independent and can be defined causally for
First Cross without importing V3 scenario identities.
