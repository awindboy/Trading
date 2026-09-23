# V10 next research contract — normalized-state forward shadow

Date: `2026-09-21`
Status: `ACTIVE NEXT CONTRACT / SHADOW ONLY / NO TRADE AUTHORITY`
Market: `GOLD# ONLY`

## 1. Objective

Determine whether a small frozen set of causal, liquidity-normalized state coordinates can identify avoidable stopped Children on genuinely new chronology without removing the persistent-run right tail.

This is not another regime, next-HA, or parameter-search project.

## 2. Frozen comparator

Keep the existing R4/R5/R7G action unchanged. The shadow layer may log hypothetical actions but may not change an EA order.

The historical training/development cutoff is:

`2026-08-28 23:57 raw M1`

Only observations strictly after that cutoff count as new evidence.

The first descriptive forward audit has now observed data through `2026-09-18 23:57`. It may evaluate the coordinates frozen in this contract, but it cannot validate a coordinate or action invented after that audit. Any later-added hypothesis starts its own future boundary after `2026-09-18 23:57`.

## 3. Frozen observations

At each existing R7G-selected Child decision, log:

```text
signal_id and effective decision timestamp
direction / k / run id / R4 and R7G weight
entry and Hard SL
H4 WMA20 OC2 direction-adjusted slope / H4 ATR180
H4 WMA20 OC2 direction-adjusted span / H4 ATR180
H1 WMA20 OC2 direction-adjusted edge / H1 ATR180
H1 WMA20 OC2 direction-adjusted span / H1 ATR180
M15 SMA60 close/OC2 support and ordering fractions
M15 WMA60 OC2 support and ordering fractions
M15 four-hour deterioration fraction
```

At exact forming-H4 +60 minutes, if the newest selected Child is still alive, also log:

```text
direction-adjusted provisional FAST-HA margin / prior completed H4 ATR180
frozen SEED1_Q10_DEFENSE hypothetical action
```

MA1 is excluded from support and penetration counts because it equals the current input.

For WMA20 OC2, `edge = current OC2 - MA20` and `span = MA1 - MA20` are identical because `MA1 = current OC2`. Preserve at most one independent interpretation; duplicate names are not independent evidence.

## 4. Frozen seed-defense action shadow

The only thresholded shadow action already frozen is:

```text
newest live R7G Child
AND r7g_weight == 1
AND exact forming-H4 +60m observation
AND normalized provisional FAST-HA margin <= -0.1641973584634039
-> hypothetical exit newest Child only
```

It does not affect 3-unit Children, older Children, entries, Hard SLs, catch-up, or actual orders.

## 5. MA-state evaluation without a gate

Do not choose an MA threshold from accumulating forward outcomes.

Evaluate the frozen continuous coordinates for:

- direction-adjusted monotonic STOP discrimination;
- calibration drift versus historical distributions;
- year/quarter and volatility-scale stability;
- incremental information beyond the provisional HA margin and existing R4/R5 state;
- concentration by direction, stage, and run;
- economic regret if a hypothetical tail were later proposed.

The historical q2.5/q20 diagnostics and H4-slope plus M15-deterioration intersection are not forward action rules.

## 6. Required outcomes

After each Child resolves, append:

```text
entry and exit timestamps
Hard SL outcome
R and raw price-PnL
FAST run length label after resolution only
L6+ right-tail membership after resolution only
seed-defense hypothetical exit R
good/bad shadow action
stop prevented
positive-Child and right-tail regret
```

Future labels may never enter live features.

## 7. Reporting

Report at minimum:

- candidate and shadow-action counts;
- baseline versus shadow Hard SL count;
- maximum and distribution of stop streaks;
- positive-Child and L6+ weighted-R retention;
- delta structural R and raw/cost-adjusted PnL;
- direction/stage/run concentration;
- uncertainty using run-block resampling;
- missing-data and execution incidents.

Judge process and regret before headline PnL.

## 8. Prohibited changes during collection

- no model-family or threshold scan;
- no rolling threshold trained from observed outcomes;
- no fixed MA breached-line rule;
- no direction or session exclusion;
- no cooldown, retry limit, minimum-R, no-chase, or campaign cap;
- no backfill of missed events;
- no use of `GOLD# 2021`;
- no claim of independent validation from 2022-2026 history.

## 9. EA lifecycle issue

Market-closed order failures from the user's MT5 run are recorded as a separate execution-lifecycle issue. They may be fixed when the EA is next upgraded, but that work must not change this research hypothesis or reinterpret closed historical actions.

## 10. Promotion boundary

Forward observation may justify a new promotion review only if stop reduction is accompanied by tolerable right-tail regret and the result is not concentrated in a few runs. Passing this contract does not automatically change the strategy or EA.
