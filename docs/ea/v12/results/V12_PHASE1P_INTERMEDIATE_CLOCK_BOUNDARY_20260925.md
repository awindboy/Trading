# V12 Phase 1P — intermediate-clock boundary result

Status: **complete and reproducible / H2 and M30 pass / research candidate only**  
Date: `2026-09-25`

## Why this phase matters

Phase 1O showed that H1 contains useful after-stop temporal information while
M15 is too noisy. Phase 1P tested the unobserved H2 and M30 clocks under the
identical causal Child, Hard-SL, history, model, threshold, fold, and capital
contract. It did not select a timeframe after seeing results.

The complete populations contain `4,246` H2 and `17,012` M30 `k=1` candidates;
the after-stop cohorts contain `1,309` and `4,820`. Two independent 11-file
packs are byte-identical and use the same `1,669,073`-row raw-M1 prefix.

## Gate result

Four H2 and six M30 models pass every frozen primary gate.

- H2: HA, static time, continuous clock, and event history.
- M30: HA, static time, continuous clock, session path, internal M5 path, and
  Wave history.

The result is not a generic HGB effect. History-only HGB fails, as do several
feature families at each clock. The useful component depends on temporal
resolution.

## Representative policies

| Clock / model | Repeat stops removed | Child retention | Tail-R retention | OOS net R | Equal-stop-budget R |
|---|---:|---:|---:|---:|---:|
| H2 continuous clock | 32.89% | 96.44% | 95.10% | 137.02 | 147.12 |
| H2 event | 34.21% | 96.22% | 95.10% | 136.18 | 146.66 |
| M30 internal M5 path | 35.29% | 95.01% | 91.71% | 234.10 | 258.46 |
| M30 session path | **37.25%** | 94.95% | 91.24% | **234.62** | **260.53** |
| Baseline H2 / M30 | — | 100% | 100% | 136.54 / 209.79 | same |

H2 stop density falls from `27.55` to about `26.59–26.77` per 100. M30 session
path falls from `28.69` to `27.21`. Win-rate gains are modest (`35.12% ->
35.40%` on H2 continuous clock; `33.76% -> 34.21%` on M30 session path), but
the policies alter only about 3–5% of all candidates and selectively remove
roughly one third of repeat stops.

## Stability audit

Every passing model remains positive in each OOS year and each pooled
liquidity tercile. M30 session path changes the OOS SHORT side from `-13.28R`
to `+3.78R` while LONG rises from `+223.07R` to `+230.84R`. M30 micro path
changes SHORT to `+2.79R` and preserves `95.47%` of LONG tail R.

Maximum stop streak is harder. M30 micro, HA, and Wave reduce it from `5 -> 4`;
M30 session path leaves the rare maximum streak at `5` despite removing 37.25%
of repeat stops. H2 continuous clock reduces `4 -> 3`; other H2 passes do not
change the pooled maximum. The mechanism reduces recurrent stopped exposure,
but does not yet guarantee that every chain ends after one or two losses.

## Resolution boundary

The evidence now describes a coherent curve:

- H4: intraday sequence compressed;
- H2: useful and stable, but fewer opportunities;
- H1: useful repeat-stop discrimination, but the 2026 fold remains negative;
- M30: best balance of opportunity, repeat-stop removal, tail preservation,
  and fold economics;
- M15: repeat stops are detectable, but local noise destroys too much tail.

M30 is therefore the leading *research clock*, not an authorized strategy.
No model score, top-quintile cutoff, session/event veto, sizing map, EA, or
trade authority is created. The next bounded question is whether the remaining
third-and-later stops in a chain can be identified without tuning on these
results.
