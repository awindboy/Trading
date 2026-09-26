# V13 HA-4 multi-timeframe standard-HA observation contract

Date: `2026-09-27`

Status: `FROZEN BEFORE HA-4 MEASUREMENT / OBSERVATION ONLY`

## Research question

HA-3 showed that changing H4 HA responsiveness exchanges persistence for
reversal lag. HA-4 asks whether the **same standard HA on a different time
scale** adds distinct causal information, rather than changing the H4 formula.

Study D1 first. Only after its separate receipt, study H1. D1 is a broader
completed state; H1 is the four completed one-hour states inside a newly
completed H4 bar. Neither timeframe may direct Baseline-0 orders.

## Frozen source and timing

Use the same GOLD# M1 source and canonical window as HA-0..HA-3. Stream M1 in
broker time and reconstruct H4, D1 and H1 raw OHLC. Check each reconstructed
timeframe against its supplied raw export; exports are parity references, not
future decision inputs. Initialize each standard-HA recursion from its first
available 2022 source bar. The first post-2024 H4 color flip starts Journey 1,
exactly as Baseline 0.

At an H4 decision, the completed H4 signal bar, the last **completed** D1 bar,
and the completed H1 bars are available. Never use the forming D1 candle or an
H1 bar after the H4 execution open. If a bar ends across a weekend, its close
becomes known only at the next actual M1 print. Decision-time context fields
and future outcome labels go to separate ledgers.

## D1, analyzed first

At every H4 decision record the last completed D1 HA color, its body/range,
opposite-wick state and same-color streak. Predefined descriptive contrasts:

- D1 color aligned versus opposed to the active H4 Journey direction;
- next H4 flip and 1/2/3-H4 continuation rates;
- the same contrasts within H4 body/range quintiles, and by year and side;
- whether a D1 feature contributes a stable distinction beyond H4 morphology,
  or mainly repeats slower price history.

Quintiles are retrospective **display bins**, not thresholds. No D1 alignment
veto, fitted score, or action is authorized.

## H1, analyzed separately after D1

At the same H4 decision timestamp record the last completed H1 standard-HA
color and how many H1 color flips occurred inside that completed H4 bar.
Predefined descriptive contrasts:

- last-H1 color aligned versus opposed to the still-active H4 Journey;
- next H4 flip and 1/2/3-H4 continuation rates;
- H1 opposite state and flip count within H4 morphology bins, year and side;
- on eventual H4 flip episodes, whether H1 opposed the old H4 color earlier,
  and how often that was a temporary interruption rather than durable lead.

An H1 flip is not called an early successful warning merely because a future
H4 flip eventually occurred. Account for all H1 warnings, including those
followed by renewed H4 continuation.

## Interpretation and gate

The primary grain is completed H4 decisions, with Journey-level coverage and
right-tail diagnostics. All 2024-2026 findings are consumed development
evidence. Overlapping H4 decisions inside a Journey are not independent
trials; report counts and avoid causal or out-of-sample language.

There is no new EA, entry, exit, SL, sizing, ML, or MT5 economic comparison in
HA-4. A signal-like association does not pass the HA-7 action gate. Advance
to HA-5 only after D1 and H1 have separate, source-backed receipts identifying
what information each adds and where it fails.
