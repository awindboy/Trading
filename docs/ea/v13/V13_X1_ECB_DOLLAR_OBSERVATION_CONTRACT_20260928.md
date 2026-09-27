# V13 X1 — ECB dollar-proxy observation contract

Date: `2026-09-28`
Status: `FROZEN BEFORE X1 OUTCOME EVALUATION / OBSERVATION ONLY`
GitHub main checked: `be88fa2be516963b2dcd196819f9b2fd026b077a`

## Question and scope

Does an information source outside GOLD# price add stable, economically useful
separation at the **birth of a standard-H4 HA Journey**? The primary target is
whether the complete Baseline-0 Journey ends with negative idealized net GOLD
price points. A secondary descriptive question is whether it identifies a
*second consecutive losing Journey* without falsely warning on the large
continuation winners.

This does not change Baseline 0, create a trade veto, or test live economics.
The full 2024-01-01 through 2026-08-28 available GOLD# window is consumed
development history. Its exact-window actual-tick MT5 economic receipt is
still pending.

## External source and deliberately limited claim

The sole new information family is the ECB daily euro reference rate in USD,
series `EXR.D.USD.EUR.SP00.A`, downloaded from the ECB Data Portal API for
2022-01-01 through 2026-08-28. It is **EUR/USD**, not DXY, a broad dollar
index, an intraday USD price, or an executable FX quote. The ECB ordinarily
publishes reference rates around 16:00 Central European time on working days.
Source and publication documentation:

- https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A
- https://data.ecb.europa.eu/help/api/data
- https://www.ecb.europa.eu/stats/policy_and_exchange_rates/euro_reference_exchange_rates/html/index.en.html

Because the broker clock's exact historical UTC offset is not established,
an ECB observation dated `D` is eligible only once the GOLD# broker-calendar
date is at least `D+2` calendar days. This conservative publication lag also
applies across weekends/holidays. No same-day ECB fixing may be used.

## Inputs and locked construction

Reuse the existing, saved HA-8A causal decision-feature ledger. Only rows with
`journey_bar == 1` enter the primary model. Do not load future labels or Child
economics until the ECB-as-of feature ledger is saved and hashed. Match each
Journey start to the most recent ECB observation eligible under the two-day
lag; carry the latest published value through non-publication days.

Define `dollar_proxy = -log(EUR/USD)` so a higher value means the dollar rose
against the euro. Exactly two causal normalized features are tested together
as one source family:

1. latest one-observation change divided by the median absolute one-step
   change among the 20 preceding published observations;
2. latest five-observation change divided by the median absolute five-step
   change among the 20 preceding published observations.

Each denominator excludes the current observation. No threshold, sign gate,
volatility regime, hour-of-day interaction, period search, or direction veto.
The two values can be constant across multiple H4 decisions; this is a real
limitation of a daily reference-rate proxy.

## Label and evaluation

- Journey outcome is the sum of all its frozen Baseline-0 Child PnLs, measured
  from the next raw-H4 open after each signal to the next Journey's first
  executable open. `loss = (sum < 0)`. The last unclosed Journey is excluded.
- Prior-Journey loss is used only for the secondary *repeat loss* diagnostic;
  its outcome is already known by the new Journey's first decision.
- Reuse HA-8A's 2024-H2, 2025-H1, 2025-H2, and 2026-to-cutoff chronological
  blocks. Before each test block, train only on prior Journeys whose exits
  were already known. 2024-H1 has no OOF prediction.
- Compare (a) training-fold base rate, (b) frozen H4 morphology plus ordered
  H1 state, (c) the same H4/H1 features plus the two ECB features. The model
  is the same fixed-penalty regularized logistic regression as HA-8A, with
  numeric imputation/standardization fitted only on the training fold.
- Report Brier, log loss, AUC and calibration overall and by block, plus
  year/side diagnostics. For a **descriptive, not actionable** highest-risk
  20% OOF bucket, report lost/winning Journey counts, repeat-loss capture,
  gross winner/loser points, total net points and >=10-bar Journey false
  warnings. Also show coverage, data age, source hashes and structural parity.

## Interpretation gate

Even a positive observation cannot authorize trading: this proxy is daily and
bilateral, the history is consumed, and actual-tick economics are incomplete.
If incremental loss separation is small or unstable, or the risk bucket still
contains large positive continuation Journeys, stop this proxy branch. Do not
search a threshold to rescue it. A genuinely intraday multi-symbol USD test
would need a new source/timing contract and is not validated by this X1 run.
