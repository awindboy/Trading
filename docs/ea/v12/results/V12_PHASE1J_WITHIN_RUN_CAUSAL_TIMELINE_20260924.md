# V12 Phase 1J — Within-run causal timeline result

Status: **complete, reproducible, consumed-development mechanism diagnostic**  
Cutoff: `2026-09-18 23:57`  
Trade/sizing authority: **none**

## Result

Phase 1J finally finds a material difference that appears *after* the first
Child enters and before the run's first stop or first `5` weighted-R touch.
This is different from the failed entry-time regime classifiers.

- Fixed population: `181` stop-only runs and `57` tail-journey runs.
- Causal timeline coverage: `234/238` runs and `6,872` completed-M15 rows.
- Four runs reached their terminal before one post-entry M15 bar completed.
- Two independent eight-file packs are byte-identical; zero post-cutoff price
  rows were parsed.

## Equal-horizon separation

The strongest early coordinate is **how much opposed excursion survived before
the close settled**, normalized by the first Child's frozen risk.

| Causal checkpoint | Feature | pooled effect | pooled AUC | F1/F2/F3 AUC |
|---|---:|---:|---:|---:|
| first completed M15 | cumulative MAE | `+0.094R` tail-minus-stop | `0.685` | `0.699 / 0.652 / 0.650` |
| second completed M15 | cumulative MAE | `+0.148R` | `0.720` | `0.734 / 0.681 / 0.689` |
| second completed M15 | signed path efficiency | `+0.499` | `0.673` | `0.658 / 0.683 / 0.729` |
| fourth completed M15 | favorable giveback | `-0.176R` | `0.707` | `0.727 / 0.682 / 0.688` |

Positive cumulative-MAE difference means tail runs had less early adverse
damage. The direction agrees in every test fold. In the after-stop subset, the
second-M15 cumulative-MAE AUC is `0.746` and signed-efficiency AUC is `0.713`,
but that subset has only `11` tail runs and cannot support a fold-level rule.

## Event sequence

Before each run's frozen terminal:

- two consecutive favorable M15 closes occur in `96.5%` of tail runs versus
  `55.2%` of stop-only runs;
- two consecutive opposed closes occur in `50.9%` versus `81.8%`;
- repaired departure occurs in `70.2%` versus `40.9%`.

Those directions repeat in F1, F2, and F3. Six repaired-departure feature pairs
pass the frozen mechanism-promotion screen. They do **not** yet pass a trading
gate: tail terminals are later than stop terminals (`685` versus `246` median
minutes), so lifetime event frequency contains right-censoring opportunity.
Equal-horizon checkpoints are the safer evidence.

## Interpretation

The useful state is not “this was a good HA at entry.” It is:

1. keep the first participation unit small;
2. observe whether the run can avoid early opposed damage and repeatedly settle
   in its own direction;
3. release later Child exposure only after demonstrated progression or repair;
4. stop adding exposure when opposed settlement persists.

This may reduce second/third stopped units without requiring an oracle that
predicts the whole H4 journey in advance. It does not justify moving or widening
the first Child's Hard SL.

## What is not proved

- No checkpoint value or event is an entry, exit, veto, or sizing rule.
- Event prevalence is not independent of time-at-risk.
- The `57` tails, especially `11` after-stop tails, are sparse.
- A staged policy may still remove most tail capital even if its class contrast
  looks clean. That must be audited directly against stopped units, tail units,
  Child frequency, win rate, and equal-stop-budget economics.

## Next frozen test

Test a no-threshold staged-funding policy on the unchanged V10 Children:

- always retain the first Child;
- compare releasing later Children only after two favorable M15 settlements;
- compare stopping later funding after two opposed settlements;
- retain first-Child-only as the broad exposure comparator;
- reject any apparent success that cuts stops and tail merely in proportion.

All chronology through the cutoff is consumed. GOLD# 2021 and post-cutoff data
remain sealed.
