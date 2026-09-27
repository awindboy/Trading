# V13 HA-8A combination model receipt

Date: `2026-09-28`
Status: `CONSUMED DEVELOPMENT / CHRONOLOGICAL OOF OBSERVATION / NO EA OR STRATEGY CHANGE`
Contract: `../V13_HA8A_COMBINATION_MODEL_CONTRACT_20260928.md`
Source: `research/v13/ha8a_combination_model.py`
Generated local audit: `output/v13_ha8a_combination_20260928/` (not in Git)

## Result in one sentence

The combination modestly improves prediction of an opposite H4 HA within
three bars, but does **not** isolate economically bad add-on Children: the
highest predicted-risk 20% still contributed positive net points, especially
because it included profitable long-Journey continuation Children.

## Scope and causal checks

- GOLD#, frozen 2024-01-01 through 2026-08-28 window; 2022-2023 warm-up.
- 4,108 decision features were built before loading 4,105 future labels.
- Raw H4 was streamed chronologically only through 2026-08-28 20:00. HA color
  was checked against every prior decision. `known_at` can be later than the
  following H4 bar's nominal start (e.g. a 00:00 H4 bar first executable at
  01:00); the following *raw H4 open* was used for idealized price parity.
- Chronological four-block expanding evaluation, with three label-unavailable
  training rows purged before each test block. OOF coverage is 3,338
  decisions, from 2024-H2 onward; 2024-H1 has no prior fit and is excluded.
- Full-window structural parity only: 965 closed Journeys, 3,858 closed
  Children, +8,147.11 GOLD price points. This is not the missing exact-window
  official real-tick MT5 receipt. It excludes real spread, slippage, costs,
  financing and actual execution failures.
- Model is fixed-penalty logistic regression; numeric preprocessing is fitted
  on past training rows only. No random split, threshold search or action test.

## Chronological OOF prediction of `flip_within_3`

Lower Brier/log loss and higher AUC are better. ECE uses fixed 0.1-wide
probability bins. These are model diagnostics, **not** trading returns.

| Frozen ladder | Brier | Log loss | AUC | ECE |
| --- | ---: | ---: | ---: | ---: |
| Training-fold base rate | 0.24639 | 0.68591 | 0.4973 | 0.0104 |
| H1 path only | 0.23380 | 0.65977 | 0.6204 | 0.0111 |
| HASTOC10 only | 0.24236 | 0.67777 | 0.5781 | 0.0319 |
| H4 morphology + H1 | 0.22608 | 0.64229 | 0.6667 | 0.0317 |
| + HASTOC10 | 0.22597 | 0.64260 | 0.6681 | 0.0325 |
| + same-slot tick activity × persistent H1 | **0.22530** | **0.64113** | 0.6702 | 0.0315 |
| + causal raw-swing state/level distance | 0.22565 | 0.64268 | 0.6712 | 0.0285 |
| + EMA50 slope/position context | 0.22549 | 0.64224 | **0.6718** | 0.0283 |

The largest incremental Brier gain over H4+H1 is only `0.00078` (activity).
Raw-swing state slightly improves pooled AUC but worsens Brier/log loss
relative to the preceding activity model. The complete stack improves AUC by
only `0.0051` over H4+H1. These small metric differences should not be read
as independent edge.

Per-block Brier shows instability:

| Test block (n) | H4+H1 | +activity | +raw swing | +EMA50 |
| --- | ---: | ---: | ---: | ---: |
| 2024-H2 (784) | 0.22227 | 0.22096 | 0.22309 | 0.22363 |
| 2025-H1 (760) | 0.22174 | 0.22155 | 0.22400 | 0.22417 |
| 2025-H2 (781) | 0.22840 | 0.22911 | 0.22600 | 0.22570 |
| 2026 to cutoff (1,013) | 0.23049 | 0.22853 | 0.22860 | 0.22778 |

No expanded family wins every chronological block. The local JSON also records
year/side and Journey-age decomposition and 0.1-bin calibration.

## Economic and right-tail diagnosis, not a simulated strategy

Of 2,355 OOF add-on Children (Journey bars 2..10) with closed-Journey
idealized economics, 1,420 lost, 934 won, one was flat, and their net was
**+6,488.49 price points**. The table shows the 471 highest predicted
`flip_within_3` risks (20%) for each model. It does **not** enact a veto.

| Risk ranking | Losses / winners | Group net | >=10-bar Journey Children | Their net |
| --- | ---: | ---: | ---: | ---: |
| H4+H1 | 286 / 185 | +1,517.90 | 66 | +3,721.51 |
| +HASTOC10 | 286 / 185 | +1,222.79 | 71 | +3,150.27 |
| +activity | 287 / 184 | **+513.61** | 66 | **+2,471.13** |
| +raw swing | 281 / 190 | +1,035.02 | 69 | +3,116.19 |
| +EMA50 | 283 / 188 | +635.10 | 67 | +2,719.35 |

The activity model's highest-risk group captures only `287/1,420 = 20.2%`
of all OOF add-on losses while containing `184/934 = 19.7%` of winners. It
has 60.9% losers versus 60.3% among all eligible Children: **almost no
loss-count concentration**. Despite a high actual three-bar flip rate
(`78.3%`, predicted `81.9%`), it remains net-positive. Its 66 long-Journey
Children did not flip within three H4 bars and supplied +2,471.13 points;
the other 405 Children contributed -1,957.52 points. That split is
**future-defined** and cannot be used as a gate.

For the activity model, descriptive risk quintiles from highest to lowest
have 471 Children each. Their flip-within-three rates are `78.3%, 66.5%,
54.1%, 46.3%, 32.3%`, so the model does rank its stated target. But their
loss counts are `287, 309, 297, 280, 247` and *all five* bins are net
positive (`+513.61, +1,235.92, +982.10, +1,743.33, +2,013.53`). There is
no safe observed loss-only bucket here.

## Decision and next question

**Do not promote this HA-8A model or any probability/quantile threshold into
Child admission, exit or sizing. Do not tune the same consumed period to
rescue it.** The H1/HA morphology baseline explains much of the short-horizon
HA flip; the extra components do not solve the economically relevant
temporary-weakness-versus-long-tail distinction. This is why HA-7's simple
warning veto failed and why a better flip predictor is not automatically a
better strategy.

If research continues, define a **separate, frozen economic lifecycle target**
at a causal decision point (for example, Child's eventual sign/magnitude or
Journey-level loss/continuation) and explicitly audit repeated losing
Journeys and large winners. Do not infer an action from the target alone.
Untouched later history and the exact-window official real-tick Baseline-0
receipt remain prerequisites to any economic promotion.

## Reproduction identifiers

- Raw H4 file SHA-256: `b080fb5463df1f80592cfeeecacc4d422069b69ac40635b912d03d97873aecbf`
- HA-4C decision features: `c6b4a1a6c2bcb32b487a3c3ac92ca2c5f85c61ea8685901b4f3271fc7346b6c9`
- HA-5 decision features: `3fa9da3c78908a3f64c4e24f6e6a7e28bf83eff17e2f7afed94670aba4108bc9`
- Frozen HA-8A feature ledger: `dc2a082cddd16359da8cb518cd535747297beecad521d40821034e0bf543be0d`
- HA-4C future labels: `bdae85a715b9102883d6af4672c98efee4c86cf1828a93d5e2e26ca74dfa7b9d`
