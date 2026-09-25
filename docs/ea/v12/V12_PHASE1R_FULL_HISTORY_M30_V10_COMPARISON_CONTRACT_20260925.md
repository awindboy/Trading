# V12 Phase 1R — full-history M30 versus V10 comparison contract

Status: **frozen before evaluation / consumed-development only**  
Frozen: `2026-09-25`

## Question

What do profit and stopped exposure look like when the frozen Phase-1P M30
session-path setup is run causally across all usable history and compared with
the frozen V10 R7G comparator?

## Causal full-history rule

The M30 policy cannot be trained on the whole sample and backfilled into 2022.
It therefore trades every M30 `k=1` candidate during 2022 as warmup, then uses
four expanding annual folds:

- train through 2022, trade 2023;
- train through 2023, trade 2024;
- train through 2024, trade 2025;
- train through 2025, trade through `2026-09-18 23:57`.

Each training row must have both its decision and outcome label available by
the fold boundary. The Phase-1P HGB parameters, HA+session-path+history fields,
and train-only top repeat-risk quintile are unchanged. Only a current `k=1`
whose immediately prior causally known `k=1` hit Hard SL can be excluded.

## Comparison boundary

Native totals are reported but are not treated as apples-to-apples because M30
uses one unit per Child and starts in 2022, while V10 R7G has variable 1/3-unit
exposure and begins on `2024-10-01`. The primary comparison also reports the
fixed V10 window through `2026-08-28 23:57`, per-100-funded-unit economics,
equal funded units, and equal stopped-unit budget.

All values are spreadless structural R. Order failures and MT5 costs are not
repaired here. The result has no trade or sizing authority.
