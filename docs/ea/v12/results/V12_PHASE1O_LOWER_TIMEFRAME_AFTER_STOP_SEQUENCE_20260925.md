# V12 Phase 1O — lower-timeframe after-stop sequence result

Status: **complete and reproducible / H1 mechanism retained / primary gate failed / no action authority**  
Date: `2026-09-25`

## Question and population

Can causally completed prior failures plus nonlinear time/session/event/path
interactions identify the next repeated stop on a lower-timeframe `k=1`
transition without broadly removing journey participation?

The model may alter only the after-stop cohort. Every other candidate remains
funded. The complete cohorts contain `2,586` H1 and `9,657` M15 candidates.
Two independent six-file packs are byte-identical.

## Main result

The answer differs sharply by timeframe.

On H1, every nonlinear information family except history alone improves repeat-
stop log loss versus the linear history control in at least two folds; HA,
static time, continuous clock, events, session path, micro path, and the full
assembly improve it in all three. The train-defined top-risk exclusion removes
roughly 35–42% of repeated stops while retaining 94–96% of all candidates and
94–98% of `>=5R` capital.

Representative pooled H1 results:

| Conditional head | Repeat stops removed | Child retention | Tail-R retention | Net R | Equal-stop-budget R |
|---|---:|---:|---:|---:|---:|
| Continuous clock | 39.78% | 94.48% | 97.52% | 80.85 | 89.07 |
| Session path | 37.02% | 95.51% | 97.52% | **90.07** | **98.52** |
| Full sequence | 34.81% | 95.73% | 97.52% | 88.23 | 95.97 |
| Unchanged baseline | — | 100% | 100% | 67.80 | 67.80 |

This is materially different from Phase 1N's broad low-risk bands. The H1
conditional policy changes only about 4–6% of all candidates, removes more than
one third of repeat stops, and preserves nearly all right-tail capital.

On M15, the same models also identify repeat stops, usually removing 38–43%.
But they retain only 76–86% of right-tail R in individual folds and pooled net-R
retention is weak. The finer clock sees more noise and again mistakes decisive
journey starts for avoidable churn.

## Why no model passes

Every H1 nonlinear temporal model passes repeat-stop, repeat-removal,
participation, and tail-preservation gates. All fail the frozen equal-stop-
budget gate because the third OOS interval remains negative. For example:

- session path: `+70.75R`, `+28.36R`, `-9.04R`;
- full sequence: `+73.05R`, `+23.36R`, `-8.17R`;
- continuous clock: `+64.56R`, `+19.05R`, `-2.76R`.

Each improves the unchanged H1 third-fold baseline of `-17.16R`, but none makes
the fold profitable. The contract required positive equal-stop-budget R in
every fold, so no result receives promotion.

M15 fails both tail preservation and equal-stop-budget economics. History-only
controls preserve capital but do not meet the repeat-removal or predictive
gates.

## Interpretation

The useful temporal scale is now bounded more precisely:

- H4 compresses intraday temporal structure too heavily;
- M15 exposes the structure but is dominated by local noise and sacrifices
  journey tails;
- H1 preserves enough session path to identify a substantial share of repeat
  stops without broad participation loss.

This is the first lower-timeframe result that directly addresses the user's
objective rather than merely reducing exposure. It remains consumed evidence,
not a rule. The 2026 loss and fixed HGB specification require independent
validation before any sizing interpretation.

No cooldown, session/news veto, threshold, HGB score, sizing map, EA, or trade
authority is granted. GOLD# 2021 and chronology after `2026-09-18 23:57` remain
sealed.
