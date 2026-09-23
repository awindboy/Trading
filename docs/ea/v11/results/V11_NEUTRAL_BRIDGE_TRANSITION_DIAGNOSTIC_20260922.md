# V11 neutral-bridge transition diagnostic

Date: `2026-09-22`

Status: `CONSUMED DEVELOPMENT EVIDENCE / ARCHITECTURE LEAD ONLY / NO TRADE, SIZING, OR PRODUCTION AUTHORITY`

> Interpretation correction: `V11_POST_STOP_CHAIN_SELECTIVITY_DIAGNOSTIC_20260922.md` is newer authority. The low admitted stop rates below came from sparse subsets that also rejected many non-stops and positive-R retries. They do not establish a successful neutral-bridge mechanism or a future-validation lead.

## Question

Can V11 reduce repeated stop chains by treating a completed NHA as an interruption rather than immediate authorization of the opposite FAST k1, and does forming Wave information add anything beyond raw price progress?

## Causal method

- Population: `2,101` first Children (`k1`) of new FAST-HA runs from the matched V10/V11 development ledger.
- Input: verified raw GOLD# M1, read once in chronological order.
- M5 and H4 were rebuilt in-stream. The `7,198` completed rebuilt H4 bars matched the retained reference with maximum numeric error `7.11e-15`; the reference file was used only after replay as a parity audit.
- Every NHA and +60/+120/+180-minute bridge observation was frozen before the current M1 row was incorporated.
- The prospective original Hard SL was checked before delayed admission. A pre-checkpoint touch killed the candidate permanently.
- Fixed clock checkpoints are mechanism probes. The causal prior-180-transition efficiency median is a normalization probe, not an optimized or authorized threshold.
- Data end: `2026-08-28 23:57`, already-consumed development history.

## Baseline anatomy

Immediate FAST k1 produced `636/2,101` stops (`30.27%`), `149.81R`, a maximum stop streak of four, `127` adjacent two-stop chains, and `33` adjacent three-stop chains.

The stopped k1 Children failed quickly: median time to stop was `183.5` minutes; `35.7%` stopped before 120 minutes, `49.2%` before 180 minutes, and `63.8%` before 240 minutes. The concentration was present in every year and on both sides. This supports the neutral-bridge problem formulation, but not a fixed cooldown rule.

## Mechanism comparison

| Observation | Attempts | Stops | Stop rate | Sum R | 2-stop chains | 3-stop chains |
|---|---:|---:|---:|---:|---:|---:|
| immediate FAST k1 | 2,101 | 636 | 30.27% | 149.81 | 127 | 33 |
| FAST k2 confirmation | 1,480 | 403 | 27.23% | 127.17 | 53 | 6 |
| first STD alignment | 1,814 | 483 | 26.63% | 159.64 | 91 | 12 |
| H4 arrival only | 278 | 55 | 19.78% | 33.74 | 3 | 0 |
| +60m raw progress | 925 | 192 | 20.76% | 128.98 | 10 | 1 |
| +60m raw progress + Wave efficiency | 696 | 127 | 18.25% | 71.24 | 4 | 0 |
| +120m raw progress | 973 | 155 | 15.93% | 97.47 | 7 | 0 |
| +120m raw progress + Wave efficiency | 716 | 85 | 11.87% | 59.51 | 4 | 0 |
| +180m raw progress | 938 | 129 | 13.75% | 79.61 | 4 | 0 |
| +180m raw progress + Wave efficiency | 690 | 72 | 10.43% | 28.56 | 2 | 0 |
| earliest qualifying 60/120/180 probe | 1,086 | 180 | 16.57% | 79.10 | 9 | 0 |

“Raw progress + Wave efficiency” requires positive directional return and forming-Wave path efficiency at or above the causal median of the prior 180 transition episodes, with a 60-episode warm-up.

## What survived the broad search

1. **Immediate opposite authorization is the structural problem.** Waiting for a second or third completed FAST HA, or for STD/SLOW alignment, reduced churn only modestly. Smoother HA confirmation does not solve the transition question.
2. **A liquidity reason helps only as context.** Same-H4 arrival was clean but admitted only `13.2%` of episodes and retained `13.9%` of L6+ runs. Generic H4-route existence admitted `98.6%` and was indistinguishable from baseline.
3. **Raw prospective progress carries most of the first separation.** Positive directional return at 60 minutes cut the stop rate from `30.27%` to `20.76%` while retaining `69.8%` of baseline positive R.
4. **Static Wave settlement is mostly redundant.** Adding settlement majority to raw progress changed the 60-minute stop rate only from `20.76%` to `20.32%`. It did not justify the Wave Candle by itself.
5. **Wave path efficiency is the only retained incremental lead.** Conditional on already-positive raw progress, higher forming-Wave efficiency remained protective in the pooled sample and in every calendar year at 60, 120, and 180 minutes. It reduced maximum stop streak to two and removed all three-stop chains in each fixed-checkpoint probe.

Conditional stop AUCs, where values below `0.5` mean higher efficiency was associated with survival, were `0.370`, `0.308`, and `0.331` at 60, 120, and 180 minutes. Every annual value was below `0.5` (`0.307-0.435`, `0.231-0.379`, and `0.249-0.432`).

This is evidence for a process semantic—efficient progress versus rotational progress—not for the specific rolling median or clock checkpoint.

## Stability and trade-offs

- The +60m progress-plus-efficiency slice was positive in every year; annual stop rates ranged from `14.19%` to `22.22%`. LONG and SHORT both remained positive (`61.36R` and `9.89R`).
- The +120m slice had lower stop rates in every year (`8.50%` to `16.28%`) but SHORT expectancy was `-3.57R` while LONG was `63.08R`.
- The +180m slice balanced side stop rates near `10.4%`, but 2022 was `-0.56R` and total retained R fell to `28.56R`.
- Taking the earliest qualifying observation across the three tested checkpoints expanded coverage to `1,086` attempts and kept the stop rate at `16.57%`, but SHORT expectancy was `-0.55R` versus LONG `79.65R`. Combining fixed reviews did not solve direction symmetry.

Thus later confirmation makes the admitted sample cleaner but increasingly pays for confidence with lost expectancy and delayed participation. No checkpoint is promoted.

## Capacity diagnostic

A consumed-data, no-cost compounding illustration supports the user's capacity thesis but cannot grant sizing authority. Immediate k1 at 1% risk ended at `3.48x` equity with `50.37%` maximum drawdown. The +60m raw-progress slice at 2% ended at `9.12x` with `38.13%` drawdown; the stricter +60m progress-plus-efficiency slice ended at `3.41x` with `27.76%` drawdown.

These numbers are descriptive only: they are in-sample, omit trading costs and execution effects, and compare different admitted populations.

## Decision

- Retain the **NHA -> neutral bridge -> authorize/resume/remain neutral** architecture.
- Reject static Wave geometry, generic route existence, and extra HA-color confirmation as standalone solutions.
- Retain **positive prospective progress plus path efficiency** as the first Wave-specific transition hypothesis worth future observation.
- Do not freeze a 60/120/180-minute delay, rolling-median threshold, admission rule, or risk multiplier.
- Research old-direction resumption as a separate branch; rejected opposite candidates cannot automatically authorize the old direction either.
- Any efficacy claim must use chronology after `2026-09-18 23:57`; the present raw source ends before that boundary and supplies no independent validation.

## Reproduction

- Script: `research/v11/analyze_v11_neutral_bridge.py`
- Ignored output: `output/v11_neutral_bridge_final_20260922/`
- Manifest records source hashes, causal reconstruction/parity audit, output hashes, and fixed diagnostic semantics.
