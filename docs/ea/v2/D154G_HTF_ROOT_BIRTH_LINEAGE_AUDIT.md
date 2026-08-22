# D-154G — HTF Root Birth Lineage Audit

Status: `PRE-REGISTERED / SHADOW-ONLY`  
Build target: `2.07R0L7 / V2_D154G_HTF_ROOT_BIRTH_LINEAGE_AUDIT`  
Authority unchanged: `docs/ea/v2/AGENTS_V2.md`

## 1. Motivation

Current V2 PLAN authorization checks that an active Root has the same direction as the current H1/M30 continuation authority and lies inside the current active map range. It does not require the Root to have been born under the same H1/M30 owner episode later frozen into PLAN.

This permits the causal question:

> Is Fill -> +1R survival worse when an actual-fill contributor Root was created during a prior owner episode on the same map timeframe later used by PLAN?

This phase moves upstream after D-154F failed to validate a universal local-M1 confirmation rule.

## 2. Observation timing

At every newly created Root, D-154G freezes only information already known at the Root creation `available_at`:

- Root TF / direction / creation event / origin time;
- Root-TF owner identity;
- H1 trend, owner ID and owner start;
- M30 trend, owner ID and owner start;
- birth-time highest mature H1/M30 primary context.

No future state is backfilled.

At actual Fill, each same-entry merged contributor scenario already contains its frozen PLAN map TF and owner ID. D-154G compares each contributor's birth snapshot with that contributor's own frozen PLAN.

## 3. Primary stale definition

For a contributor scenario:

```text
plan_map_tf = frozen H1 or M30 authority used by PLAN
plan_owner  = frozen owner ID used by PLAN

STALE PRIOR OWNER
= at Root birth, plan_map_tf already had a mature owner
  AND birth owner ID != frozen plan_owner
```

Direction is reported separately as SAME_DIR or OPPOSITE_DIR.

The fill-level primary exposure is:

```text
HAS_PRIOR_SAME_TF_OWNER
= at least one actual-fill contributor satisfies the stale definition
```

Same-entry merged contributors remain one Fill outcome. Contributor rows are descriptive and are never treated as independent trades.

## 4. Explicit non-stale exception

A Root may be created while H1 is NEUTRAL/TRANSITION and same-direction M30 is mature, then later participate after a new H1 owner is established. This is classified:

```text
M30_TO_H1_PROMOTION
```

and is **not** labeled stale in D-154G. This prevents a legitimate lower-to-higher timeframe maturation path from being mixed with a prior-owner episode.

## 5. Pre-registered primary hypothesis

> Actual fills with `HAS_PRIOR_SAME_TF_OWNER` have lower Fill -> +1R survival than fills with no prior-same-TF-owner contributor.

Outcome remains the D-151 exact barrier ordering:

```text
PLUS_1R
SL_FIRST
RIGHT_CENSORED
```

Right-censored observations are excluded from resolved rates and never reconstructed.

## 6. Secondary descriptive taxonomy

Contributor classes may include:

- `SAME_PLAN_TF_OWNER_AT_BIRTH`
- `PRIOR_SAME_TF_OWNER_SAME_DIR`
- `PRIOR_SAME_TF_OWNER_OPPOSITE_DIR`
- `M30_TO_H1_PROMOTION`
- `H1_CONTEXT_BEFORE_M30_PRIMARY_*`
- `NO_DIRECTIONAL_PRIMARY_AT_BIRTH`
- other / missing instrumentation classes.

These are not threshold candidates. Root age is logged only descriptively; no age cutoff may be mined.

## 7. Research configuration

```text
EXTERNAL_CONTINUATION baseline
V3E BANK_2R_LOCK_ONE as provisional post-+1R reference
EM OFF
D151 ON
D154A/B/C/F OFF
D154G ON
Every tick based on real ticks
fixed risk money $100
```

SP does not define the D154G primary outcome because Fill -> +1R / original-SL ordering occurs before the post-+1R management question.

## 8. Discovery / validation separation

Discovery:

```text
GOLD23: 2023-01-01 .. 2023-12-21
```

The final date avoids the known 2023-12-22 market-closed cancel fault. Any end-window open observation remains right-censored.

Validation is frozen before discovery interpretation:

```text
GOLD24
GOLD25
BTCUSD25
SILVER25
CADJPY25
```

Do not run validation until discovery is reviewed.

## 9. Prohibited rescue paths

Do not add:

- Root-age thresholds;
- source-TF-specific vetoes;
- LONG/SHORT-specific rules;
- market-specific exceptions;
- H1/M30 score combinations;
- wave-progression or event-count thresholds;
- outcome-known filtering.

If the stale-owner relation fails independent validation, reject it and move to a different HTF premise representation question rather than tuning the definition.

## 10. Strategy authority

D-154G may record and classify only. It may not change PLAN, Root eligibility, Root contact, sweep, CHoCH, FVG, Entry, SL, TP, sizing, order lifecycle, SP or EM.
