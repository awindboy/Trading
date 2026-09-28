# V13 HA-9 runner/tactical role receipt

Last synchronized: `2026-09-28`
Status: `CONSUMED DEVELOPMENT + POST-CUTOFF QUASI-HOLDOUT / REJECTED / NOT ACTION AUTHORITY`

## 1. Question

Can an already-proven add-on become a longer-horizon runner while later
add-ons remain tactical? Separately, should new add-ons be suppressed while an
existing runner remains open?

A Child is eligible only after its causal proof timestamp. Runner exits are
predeclared FAST-R25 H4 or standard-H4 exits. Child #1 remains actual HA-9.

## 2. First proven add-on as runner

| Policy | Runner Children | Wins | Losses | WR | Net USD | DD | Max streak |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Actual HA-9 | 0 | 2,118 | 1,734 | 54.98% | +3,067.50 | 1,313.10 | 14 |
| First proven -> FAST-H4 | 521 | 1,909 | 1,944 | 49.55% | +5,780.22 | 1,417.42 | 19 |
| Rolling proven -> FAST-H4 | 635 | 1,861 | 1,993 | 48.29% | +5,596.30 | 1,410.80 | 19 |
| First proven -> STD-H4 | 521 | 1,894 | 1,959 | 49.16% | +5,369.54 | 1,513.69 | 19 |

The first-proven FAST version changes its 521 runner Children from 475 wins / 45
losses under actual HA-9 to 266 wins / 255 losses. Net rises by `$2,712.72`
because a small right tail becomes much larger, but 210 additional losing
Children, five more consecutive losses and higher DD directly violate the
active objective.

This is the same economic trade-off seen in the global FAST-H4 matrix, merely
concentrated into one Child per Journey.

## 3. Breakout acceptance is narrower but still not a loss-quality edge

Requiring an aligned completed-H1 close beyond the proof extreme before runner
activation leaves only 56 consumed-period runner Children:

```text
actual:        49 wins / 7 losses, +$1,286.61
FAST runner:   39 wins / 17 losses, +$1,596.59
```

Combined result:

| Policy | Wins | Losses | WR | Net USD | DD | Streak |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Actual | 2,118 | 1,734 | 54.98% | +3,067.50 | 1,313.10 | 14 |
| Accepted first runner | 2,108 | 1,744 | 54.72% | +3,377.48 | 1,271.50 | 14 |

Net improves in all three consumed years and DD does not worsen by year, but
loss count increases in every year (`+4`, `+2`, `+4`). The mechanism again
creates larger tails by converting ten quick winners into longer-horizon
losses.

In the short post-cutoff overlap, only two Children qualified. Both were actual
winners totaling `+$15.06`; FAST management produced one win and one loss
totaling `-$7.19`. Combined net changed from `+$7.13` to `-$15.12`, losses rose
from 48 to 49, and DD rose from `$477.37` to `$499.62`.

The sample is small, but it provides no basis to tolerate the consumed-period
loss-count increase.

## 4. Suppressing new add-ons while a runner lives

| Policy | Selected | Skipped wins | Skipped losses | WR | Net USD | DD | Streak |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| First FAST runner + suppress | 2,416 | 906 | 534 | 41.57% | +4,935.85 | 1,242.31 | 18 |
| Rolling FAST runner + suppress | 2,234 | 1,021 | 600 | 37.62% | +4,696.90 | 1,259.37 | 18 |
| First STD runner + suppress | 1,971 | 1,181 | 701 | 36.17% | +4,312.10 | 1,256.13 | 18 |

Suppression removes far more winners than losses. The remaining net is carried
by runner right tails while ordinary win rate and loss streak quality collapse.
This is not evidence that runner occupancy identifies bad new add-ons.

## 5. Late-Child diagnosis

Canonical C10 is negative (`88` trades, 60.71% WR, `-$72.85`), but ordinal
performance is not monotonic:

```text
C2 +$57.63    C3 +$399.38   C4 +$11.14
C5 +$175.59   C6 +$56.82    C7 +$161.30
C8 +$353.63   C9 +$61.83    C10 -$72.85
```

C4 is nearly flat while C7–C9 are profitable. Therefore `late Journey` is not
a sufficient causal veto and C10 alone cannot justify a fitted ordinal rule.

## 6. Decision

Rejected:

- first-proven or rolling FAST/STD runner conversion;
- H1-acceptance runner conversion;
- suppressing new tactical add-ons merely because a runner exists;
- a C10-only or arbitrary late-Child veto;
- sizing up a runner state that has not separated loss quality.

The conceptual distinction between retention and new-add permission remains
valid, but the tested HA/proof/acceptance information does not identify a
runner with the required ordinary-equity edge.

## 7. Reproduction artifacts

- `research/v13/ha9_runner_tactical_audit.py`
- `output/v13_ha9_runner_tactical_20260928/summary.json`
- post-cutoff runner reconstruction in
  `research/v13/ha9_timeout_extension_holdout.py`
