# V12 Phase 1N — lower-timeframe temporal-information result

Status: **complete and reproducible / consumed-development diagnostic / no action authority**  
Date: `2026-09-25`

## Question

Does lowering the observation clock from H4 to H1 or M15 make the temporal
information compressed inside H4 useful for separating stopped transitions from
right-tail journeys?

This was not a faster V10 replay. Every H1 and M15 FAST `k=1` transition was
enriched with static time, continuous local clocks, economic-event distance and
released surprise, Asia/London/New-York source-box paths, CRT Parent state,
internal M15/M5 path, and Wave price-time distribution. Ten frozen ablations
were evaluated with three expanding out-of-time folds and label-availability
cutoffs.

## Population and reproducibility

- H1 `k=1`: `8,666` resolved candidates; `29.90` stopped units per 100 and
  `+216.17R` over the complete consumed population.
- M15 `k=1`: `34,519` candidates; `27.98` stopped units per 100 and `+261.69R`.
- Both independent 16-file packs are byte-identical.
- `1,669,073` raw M1 rows were parsed through `2026-09-18 23:57`; the prefix
  hash is `04e074...4c939` and no later price was parsed.
- A compliance audit found one unresolved label at each training boundary in
  each population. The initial model outputs were discarded; the final packs
  require both decision time and `label_available_at` to precede the training
  boundary, including inner model selection.

## Frozen predictive screen

Only three ablations improved both Hard-SL and `>=5R` log loss versus HA-only
in at least two of three folds:

- H1 HA + internal M15 path;
- H1 HA + static session/weekday/hour;
- M15 HA + static session/weekday/hour.

Continuous clock, event proximity/surprise, complete session path, CRT Parent,
Wave, all-time information, and the full assembly all failed the joint screen.
More information and more complex assembly were not better.

## Capital and repeated-stop audit

The passing predictive heads do not pass an economic interpretation:

| Population / head | Q5 child retention | stop retention | net-R retention | `>=5R` retention | Q5 stop/100 |
|---|---:|---:|---:|---:|---:|
| H1 + M15 path | 19.37% | 5.12% | 34.80% | **0.00%** | 7.60 |
| H1 + static time | 18.75% | 4.35% | 31.93% | **0.00%** | 6.68 |
| M15 + static time | 21.46% | 5.57% | 4.40% | **3.03%** | 7.21 |

The maximum OOS stop streak falls from `4 -> 2` on H1 static time and from
`5 -> 2` on M15 static time, but only after removing about four-fifths of all
candidates. H1 static time retains `3.02%` of recurrent stops, `5.33%` of
isolated stops, and `24.56%` of non-stops. M15 retains `5.67%`, `5.51%`, and
`27.57%`, respectively. It separates stops from non-stops, but does not
meaningfully separate recurrent from isolated stops.

The retained Q5 net R is negative in the first fold for every passing family.
H1 passing bands retain no `>=5R` capital at all; M15 static time retains only
`3.03%`. This is the exact failure mode the research was meant to avoid:
substantial stop reduction produced by broad exposure removal while decisive
journeys disappear faster than stopped exposure.

## Interpretation

Lowering the timeframe was still informative. Internal H1 formation has a
stable relationship with immediate stop risk: the highest-conviction H1 band
has more aligned M15 closes, larger directional net, higher path efficiency,
fewer internal transitions, and stronger body efficiency. Static time also
contains a reproducible stop-frequency coordinate.

But the new temporal dimensions do not yet identify *why* a transition is the
start of a journey. Additive event/session/path descriptions do not protect the
rare right tail, and the current score mostly discovers low-volatility,
low-opportunity states. No session, weekday, hour, event, path, CRT, Wave,
threshold, veto, or sizing rule is promoted.

## Next bounded question

The next unit is not another broad admission score. Within H1/M15 `k=1`, test
the conditional state after a causally completed stopped transition and model
whether the next opposite transition also stops. Use prior-failure cadence and
nonlinear time/session/event/path interactions, while leaving every candidate
outside the after-stop cohort unchanged. Success requires selective removal of
repeat stops with tail and equal-stop-budget preservation in every fold.

All observations remain consumed development evidence. GOLD# 2021 and prices
after the cutoff remain sealed. Phase 1N grants no entry, veto, sizing, EA, or
trade authority.
