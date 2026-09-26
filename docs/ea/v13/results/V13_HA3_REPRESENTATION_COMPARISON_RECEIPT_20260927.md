# V13 HA-3 representation comparison receipt

Date: `2026-09-27`

Status: `OBSERVATION COMPLETE / NO REPRESENTATION PROMOTED`

The formulas and window are fixed in
`../V13_HA3_REPRESENTATION_COMPARISON_CONTRACT_20260927.md`.
Source SHA-256 and causal/H4 parity are recorded in the HA-0 receipt.
Reproduce with `research/v13/ha_representation_audit.py`; local generated
decision and outcome ledgers are under `output/v13_ha3_20260927/`.

## What HA-3 was trying to learn

HA-2 isolated a tension inside standard HA: holding a color through temporary
pullbacks preserves large Journeys, but confirming a real turn late gives back
part of the favorable move. HA-3 asked whether this is a fundamental
**persistence versus reversal-lag exchange** in the HA representation, or a
peculiarity of the standard formula. FAST-R25 reduced recursive memory;
EMA2 added smoothing. Neither was proposed as a trading rule.

We measured both sides of each change: how quickly a variant ends a Journey
*and* how often its new color survives another 1/2/3 H4 bars. If an earlier
flip is mostly a one-bar interruption, shorter exit lag alone has not solved
the problem. Conversely, fewer short runs may be bought by recognizing a real
turn later. A strategy judgment needs matched price episodes and actual-tick
economics, not just a table of separately partitioned Journeys.

| Representation | Closed Journeys | Child decisions (cap 10) | 1-bar | >=10-bar | Raw extreme→exit median | Giveback median (GOLD price) |
|---|---:|---:|---:|---:|---:|---:|
| Standard HA | 965 | 3,858 | 187 | 88 | 7.35h | 21.41 |
| FAST-R25 | 1,240 | 4,004 | 315 | 46 | 6.40h | 18.03 |
| PRE-EMA2 | 757 | 3,623 | 95 | 122 | 8.83h | 24.10 |
| POST-EMA2 | 757 | 3,623 | 95 | 122 | 8.83h | 24.10 |

New-color survival for another 1/2/3 H4 bars:

```text
STD       80.6% / 59.7% / 45.3%
FAST-R25  74.6% / 48.9% / 34.0%
EMA2      87.5% / 70.3% / 54.4%
```

Child decisions are a hypothetical one-per-bar count, not actual fills for a
variant EA. FAST disagreed with STD color on 9.42% of common decision bars and EMA2 on
8.74%. FAST reduced median raw-extreme-to-exit time by 0.95h but generated
275 additional closed Journeys and 128 additional 1-bar Journeys. EMA2 cut
closed Journeys by 208 but delayed the median exit 1.48h and increased median
giveback by 2.69 GOLD price. These are **different episode partitions**;
the giveback medians cannot be subtracted as a matched-trade profit benefit.

As shares of their own closed Journeys, one-bar runs were 19.4% for STD,
25.4% for FAST, and 12.5% for EMA2. The faster representation reacts sooner
but fragments more of the price path. The smoothed one preserves longer runs
but pays more delay. The expected mechanism appears in this consumed dataset;
it does not identify which cost is economically preferable.

PRE-EMA2 and POST-EMA2 produced **zero color differences across all 4,108
decision bars**. This is expected under these exact linear EMA/HA formulas
and matched initial seeds: applying the same linear EMA to each raw OHLC before
the HA linear recurrence commutes with smoothing the resulting HA Open/Close.
Their synthetic wick geometry need not be identical, but they are not two
independent color candidates here.

The basic trade-off is real in the consumed development history: faster
recursion buys a shorter median exit lag while fragmenting more runs; added
smoothing suppresses short runs while raising exit lag. Neither side is an
economic winner without matched-episode participation and official actual-
tick testing. No baseline EA change, filter, or sizing change is authorized.

In particular, HA-3 did **not** establish that a faster HA can distinguish a
real reversal from a temporary pullback at decision time. It shows what
happens when responsiveness is changed blindly. Solving the HA-2 giveback
problem would require an additional causal distinction, not just the label
FAST or a different smoothing order.

Next: HA-4 D1 standard-HA context, then H1 separately, observation-only.
