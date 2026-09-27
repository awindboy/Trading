# V13 HA-6B moving-average context observation receipt

Date: `2026-09-27`
Status: `HA-6B1/HA-6B2 OBSERVATION COMPLETE / DEVELOPMENT EVIDENCE / NO ACTION AUTHORITY`
GitHub authority base: `40f97352e47c66cd3b952f74532b1b71969e79fd`

## Scope

HA-6B tested one moving-average family in two attribution-preserving steps on the unchanged Standard-H4 Baseline-0 population.

- HA-6B1: raw H4 Close EMA50 level/slope context only.
- HA-6B2: raw H4 High/Low EMA20 directional envelope only, measured after HA-6B1.
- No EMA period search, no trade filter, no exit, no Child change and no combined EMA strategy.
- H4 SHA256: `5e12fa91f974c0f15e340ea8116bd9168fc6821e6309592cee1a7e197675de09`
- H1 SHA256: `c1d9f63f8af4d7dddd9e20e6eb124dc71de51015384b9c61a772d5981c7be52c`
- 4,105 labeled H4 decisions / 964 labeled Journeys, preserving the HA-4C/HA-5 population.

External lead: MQL5 Article 20851 (`https://www.mql5.com/en/articles/20851`). It uses `EMA50 PRICE_CLOSE` slope as broad trend context and `EMA20 PRICE_HIGH/PRICE_LOW` as local boundaries. V13 split those mechanisms instead of importing its combined signal rules.

## HA-6B1 — EMA50 context

### Raw descriptive separation

- EMA50 slope opposed to Journey: 1,360 decisions, next-H4 flip **29.71%**.
- EMA50 slope aligned: 2,745 decisions, next-H4 flip **20.36%**.
- HA Close on the Journey-opposed side of EMA50: 1,451 decisions, next-H4 flip **26.95%**.
- HA Close on the Journey-aligned side: 2,654 decisions, next-H4 flip **21.55%**.

The side-normalized EMA50-slope quintiles were ordered descriptively: next-H4 flip fell from **29.96%** in the weakest quintile to **15.59%** in the strongest. Remaining favorable excursion generally increased with more aligned context.

### Increment beyond prior V13 state

Within comparable H4 morphology, Delta/wick, ordered-H1, HA-5 raw-swing and HA-6A HASTOC-tertile cells:

- slope opposition minus alignment: **+3.07pp next-H4 flip**, **+8.78pp flip-within-3**, on 2,562/4,105 decisions;
- position opposition minus alignment: **+2.86pp next-H4 flip**, **+8.85pp flip-within-3**, on 2,586/4,105 decisions.

This is compatible with EMA50 contributing a slower-horizon context dimension, but the next-bar increment is modest and overlap is incomplete.

### H1-opposition question

Among 1,395 last-H1-opposed decisions, EMA50 slope opposition showed 51.35% next-H4 flips versus 44.64% when aligned. After H4 morphology, HA-5 and HASTOC context, the comparable overlap retained roughly +2.7pp next-H4 and +13.6pp three-H4 separation, but only 738/1,395 decisions were in supported cells. This remains development description, not an exit rule.

### Tail counterexample

For the 88 Journeys lasting at least ten Standard-H4 bars:

- EMA50 slope opposition occurred in **37/88** long Journeys, 129 decisions;
- **128/129** did not flip next H4;
- median favorable movement still remaining after those warnings: **3.44 trailing-H4 ranges**.

EMA50 position opposition similarly appeared in 38/88 long Journeys; 152/153 warnings did not flip next H4. Therefore an EMA50 alignment gate or exit would cut important tails.

At Journey birth, slope-aligned births produced >=10-bar Journeys in 53/498 cases (10.6%) versus 35/466 (7.5%) when opposed. The difference is interesting as broad context, but 35 of the 88 long Journeys were born with slope opposition, so it is not a safe admission veto.

## HA-6B2 — EMA20 High/Low envelope

Define the Journey-directional boundary from raw-price EMA20 High for LONG and EMA20 Low for SHORT; observe whether completed HA Close lies beyond it.

### Raw descriptive separation

- not beyond directional EMA20 boundary: 1,807 decisions, next-H4 flip **27.56%**, three-H4 flip **62.09%**;
- beyond boundary: 2,298 decisions, next-H4 flip **20.23%**, three-H4 flip **52.00%**.

The side-normalized boundary-distance quintiles also showed broad ordering: next-H4 flip was **26.67% / 28.01% / 24.36% / 21.68% / 16.57%** from weakest to strongest quintile. This direction appeared in all six year×side diagnostic slices.

### Increment beyond prior V13 state

After H4 morphology + Delta/wick + ordered-H1 + HA-5:

- not-beyond minus beyond: **+3.16pp next-H4**, **+8.17pp three-H4** on 3,532 decisions.

After additionally conditioning on HASTOC:

- **+3.82pp next-H4**, **+10.58pp three-H4** on 2,397 decisions.

After additionally conditioning on EMA50 slope and position:

- **+3.57pp next-H4**, **+9.35pp three-H4** on only **1,020/4,105 decisions (24.8%)**.

Thus some local-extension information may remain, but support becomes thin when all prior state is held comparable.

Within the 1,395 last-H1-opposed decisions, the fully conditioned comparison had only **41 rows in 2 eligible cells**, so HA-6B2 does not establish an independent solution to the H1 false-warning problem.

### Tail counterexample

In >=10-bar Journeys, HA Close failed to exceed the directional EMA20 boundary in:

- **62/88** long Journeys;
- 191 warning decisions;
- **190/191** did not flip next H4;
- median favorable movement still remaining: **3.88 trailing-H4 ranges**.

This is incompatible with a safe EMA20-based exit or hard continuation gate.

## Interpretation

The moving-average family is not useless, but its role is narrower than common HA+EMA strategy examples imply.

1. EMA50 carries a slower regime/context dimension; its strongest residual separation is over a several-H4 horizon rather than the immediate next H4.
2. EMA20 High/Low carries local extension information and remains directionally consistent across year/side diagnostics, but much of its apparent effect overlaps existing HA/H1/raw-swing/HASTOC/EMA50 state.
3. Both families produce severe false warnings inside economically important long Journeys. They do **not** justify an alignment filter, exit, Child skip or EMA-combination strategy.
4. The odd four-state EMA50 pockets are descriptive only: `position_only` had 40 observations and high next-flip incidence, while `slope_only` had 131 and low incidence. These small, structurally different transition pockets are not thresholds or rules.

HA-6B therefore stops at observation. Retain EMA50 slope/position and EMA20 directional-boundary distance as possible later state features, but do not change Baseline 0.

Per the current roadmap, the next distinct family is **HA-6C: ATR as normalization, not signal**. Its purpose should be to determine whether the apparent morphology/EMA/HASTOC relations are stable after placing distances and excursions on a volatility-aware coordinate, without creating an ATR gate.
