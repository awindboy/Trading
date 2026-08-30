# V8-B2 Source-of-Move / Cross-Market Direction Research Contract

Date: `2026-08-31`
Status: `PRE-REGISTERED / DATA-ACCESS BLOCKED`
Production authority: `NONE`
Direction authority: `NONE`
V8-A: `FROZEN`
GOLD# 2021: `LOCKED / UNTOUCHED`

## 1. Why V8-B2 exists

After strict causal correction, endogenous GOLD chart/indicator history does not provide stable strong same-horizon direction information.

At the same time, V8-A demonstrates that near-term movement intensity is strongly learnable.

This creates a specific failure mechanism rather than a generic invitation to add features:

> The GOLD chart contains substantial information about **whether the market is ready to move**, while the **sign of the next expansion** may depend more on information arriving through USD, rates, cross-gold markets, macroeconomic surprise or other source-of-move channels.

V8-B2 therefore tests whether a small, mechanism-linked external context adds directional information beyond the strictly causal GOLD-only control.

This is not an unrestricted external-variable tournament.

## 2. Literature motivation — hypothesis support, not strategy validation

Prior high-frequency gold research reports that:

- U.S. macroeconomic news surprises can affect gold returns, volatility and volume quickly;
- unexpectedly stronger U.S. economic news often has a negative short-horizon gold response;
- FOMC/monetary-policy shocks create asymmetric intraday gold return and volatility responses;
- gold, Treasury rates and other markets can exhibit news-driven co-jumps.

Relevant background includes:

- Christie-David, Chaudhry & Koch (2000), *Do macroeconomics news releases affect gold and silver prices?*
- Elder, Miao & Ramchander (2012), *Impact of macroeconomic news on metal futures*.
- Awartani, Hussain & Virk (2024), *How do the gold intra-day returns and volatility react to monetary policy shocks?*
- Semeyutin & Downing (2022), *Co-jumps in the U.S. interest rates and precious metals markets and their implications for investors*.

These papers motivate looking outside GOLD's own lagged OHLC for sign information. They do not validate any V8-B2 feature or threshold.

## 3. Frozen target

V8-A remains unchanged.

For each factual V8 event and H in `{15,30,60}`:

```text
p_H = frozen V8-A P(+/-10 move within H)
```

V8-B2 continues to test conditional side only:

```text
q_H = P(UP first | a +/-10 move occurs within H, causal information at t)
```

Full-population scoring remains mandatory:

```text
P(NO MOVE) = 1-p_H
P(DOWN)    = p_H * (1-q_H)
P(UP)      = p_H * q_H
```

No model may be promoted from mover-only AUC.

## 3.1 Mandatory causal alignment implementation guard

The correction pack includes:

```text
research/ea/v8/v8_causal_time_alignment.py
research/ea/v8/test_v8_causal_time_alignment.py
```

The synthetic regression deliberately places extreme future values inside the unfinished H1/M15 bar after a 10:25 decision. The test passes only when:

- completed H1/M15 selection is based on explicit availability time; and
- current partial H1/M15 OHLC uses M1 rows strictly before 10:25.

V8-B2 must keep this test passing before any cross-market outcome is opened.

## 4. Controls

Every experiment must compare against:

### C0 — V8-A + no direction model

```text
UP/DOWN split by prior or 50/50
```

### C1 — corrected causal GOLD-only V8-B control

Use the corrected completed-only GOLD feature contract, not the invalidated leaky table.

### B2 — GOLD + external source-of-move context

Only incremental improvement of B2 over C1 is attributable to external information.

## 5. Initial external information set

The initial dataset is deliberately small and tied to mechanisms already available in the project's consumed development panel.

### Primary source 1 — USDJPY#

Role:

- proxy for rapid USD / U.S.-rate pressure visible in the broker market panel;
- not assumed to be a pure DXY or rate proxy because JPY-specific shocks also exist.

Use causal signed movement and state only. No hand-written `USDJPY up => gold down` rule.

### Primary source 2 — XAUEUR#

Role:

- gold priced outside USD;
- helps distinguish broad metal-direction pressure from USD translation effects.

A move that is coherent in XAUUSD and XAUEUR is economically different from a move concentrated in the USD quotation alone.

### Negative-control source — BTCUSD#

Role:

- broad risk/sentiment market control already present in the consumed panel;
- not granted special gold-direction semantics.

If BTC improves results while the mechanism-linked USDJPY/XAUEUR variables do not, treat that as a warning of generic overfitting rather than an automatic discovery.

## 6. Frozen first feature family

For each external symbol, construct causal M1-prefix features at the GOLD decision timestamp.

Initial signed horizons:

```text
5 / 15 / 30 / 60 / 120 / 240 minutes
```

Per-symbol features:

- normalized signed close displacement;
- close location in rolling high-low range;
- path efficiency = net displacement / total absolute displacement;
- body-direction bias;
- realized range / activity magnitude as context, but not as an outcome-selected gate.

Cross-market relations:

- GOLD vs XAUEUR signed agreement/disagreement;
- GOLD vs USDJPY signed co-movement;
- short-horizon change in those relationships;
- no manually tuned thresholds.

Do not add dozens of indicators in the first run.

## 7. Strict timestamp boundary

At GOLD decision time `t`:

### M1

Only external M1 rows with timestamp `< t` may enter the observation.

### Resampled higher timeframe, if later used

A completed bar is available only when:

```text
bar_start + duration <= t
```

If a partial bar is desired, rebuild it from raw M1 rows `< t`; never use a later full-bar OHLC.

### Cross-market gaps

Do not forward-fill an external price across an unlimited market closure or missing-data interval.

Record age since the last external observation. First B2 implementation should fail/mark unavailable when a frozen maximum age is exceeded rather than silently create stale context.

The maximum-age rule must be determined from timestamp/data-quality structure before direction outcomes are inspected.

## 8. Development allocation

Known historical raw-data lineage documents that the consumed panel contains:

```text
GOLD#    2023-2025
USDJPY#  2023-2025
XAUEUR#  2023-2025
BTCUSD#  2023-2025
```

and a later working dataset contains:

```text
GOLD#    2026 YTD
USDJPY#  2026 YTD
BTCUSD#  2026 YTD
```

The exact raw bytes must be mounted and hash-verified before B2 outcome work.

Do not substitute unrelated web price data for the broker panel during the first B2 test.

## 9. Chronological evaluation

If only the 2023-2025 common panel is mounted:

```text
train 2023       -> eval 2024
after design freeze:
train 2023-2024  -> eval 2025
```

2025 is not used to rescue a failed 2024 specification.

If exact 2026 USDJPY/BTC and a comparable 2026 cross-gold source become available, 2026 may be an additional open-development diagnostic only after the B2 feature contract is frozen.

GOLD# 2021 remains untouched.

## 10. Evaluation metrics

Report for every horizon and year:

- mover-only conditional AUC, diagnostic only;
- full-population 3-class log loss;
- full-population multiclass Brier score;
- non-overlap conditional AUC;
- event-family breakdown;
- week-block uncertainty where population permits;
- incremental delta versus corrected GOLD-only C1;
- incremental delta versus C0.

Primary evidence is **full-population proper scoring improvement**, not the prettiest mover-only subgroup AUC.

## 11. Promotion gate

B2 may continue to a shadow model only if all are true:

1. no causal-alignment or source-age violation;
2. B2 improves full-population proper score over corrected GOLD-only C1 in both future-hidden evaluation years available;
3. conditional side ranking does not reverse materially across evaluation years;
4. outcome-blind non-overlap result remains directionally consistent;
5. improvement is not carried only by BTC negative-control features;
6. no event-family threshold rescue is required.

No fixed minimum AUC is introduced after seeing results.

## 12. Hard failure / no-rescue rules

If 2024 fails:

- do not tune feature windows using 2024 direction outcome;
- do not add RSI/EMA/CCI variants;
- do not choose only one profitable session;
- do not delete inconvenient event families;
- do not change +/-10 barrier;
- do not alter V8-A.

If 2024 passes but 2025 reverses:

- classify the original B2 hypothesis as unstable;
- do not tune on 2025 to restore it.

## 13. Data-access status at contract creation

The active research runtime currently has the full GOLD# 2022-2026 M1 source but not the raw external-market M1 files as mounted bytes.

File-library manifests confirm the external raw lineage and hashes, but referenced manifests/derived ledgers are not substitutes for raw M1 data.

Therefore B2 is currently:

`PRE-REGISTERED / BLOCKED ON RAW EXTERNAL M1 MOUNT`

Once the exact raw external input is available, run data-quality/alignment preflight first. Do not alter this contract after seeing B2 direction outcomes.
